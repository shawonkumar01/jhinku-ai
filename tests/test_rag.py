
from unittest.mock import patch

from app import models
from app.ai import prompts, rag
from app.ai.rag import RagResult


def _make_chatbot(db_session, org_id=1):
    chatbot = models.Chatbot(
        organization_id=org_id,
        name="Bot",
        public_widget_id="widget123",
        is_active=True,
    )
    db_session.add(chatbot)
    db_session.commit()
    db_session.refresh(chatbot)
    return chatbot


class TestPromptBuilding:
    def test_context_is_delimited_as_untrusted(self):
        messages = prompts.build_messages(
            "What is the refund policy?",
            ["Refunds are allowed within 30 days."],
        )
        user_msg = messages[1]["content"]
        assert "<reference_material>" in user_msg
        assert "untrusted" in user_msg.lower()
        assert "refund" in user_msg.lower()

    def test_system_prompt_override(self):
        messages = prompts.build_messages(
            "Hi", [], system_prompt="You are a pirate."
        )
        assert messages[0]["content"] == "You are a pirate."

    def test_no_context_still_asks_question(self):
        messages = prompts.build_messages("Hello?", [])
        assert "Hello?" in messages[1]["content"]


class TestRagGuardrails:
    def test_fallback_when_embedding_fails(self, db_session):
        chatbot = _make_chatbot(db_session)
        with patch(
            "app.ai.rag.embeddings.embed_query",
            side_effect=RuntimeError("no key"),
        ):
            result = rag.answer_question(db_session, chatbot, "Hi?")
        assert result.used_fallback is True
        assert result.answer == prompts.FALLBACK_ANSWER

    def test_fallback_when_no_relevant_chunks(self, db_session):
        chatbot = _make_chatbot(db_session)
        with patch(
            "app.ai.rag.embeddings.embed_query",
            return_value=[0.1] * 1536,
        ), patch(
            "app.ai.rag.retrieval.search_chunks",
            return_value=[],
        ):
            result = rag.answer_question(db_session, chatbot, "Hi?")
        assert result.used_fallback is True

    def test_fallback_when_chunks_too_distant(self, db_session):
        chatbot = _make_chatbot(db_session)
        fake_chunk = models.KnowledgeChunk(
            organization_id=1,
            knowledge_source_id=1,
            content="irrelevant",
            chunk_index=0,
        )
        # distance 0.9 > RAG_MAX_DISTANCE 0.5
        with patch(
            "app.ai.rag.embeddings.embed_query",
            return_value=[0.1] * 1536,
        ), patch(
            "app.ai.rag.retrieval.search_chunks",
            return_value=[(fake_chunk, 0.9)],
        ):
            result = rag.answer_question(db_session, chatbot, "Hi?")
        assert result.used_fallback is True

    def test_answer_with_sources(self, db_session):
        chatbot = _make_chatbot(db_session)
        source = models.KnowledgeSource(
            organization_id=1,
            title="FAQ",
            original_filename="faq.txt",
            file_path="/tmp/x",
            file_size=10,
        )
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)

        chunk = models.KnowledgeChunk(
            organization_id=1,
            knowledge_source_id=source.id,
            chatbot_id=chatbot.id,
            content="Refunds within 30 days.",
            chunk_index=0,
        )
        db_session.add(chunk)
        db_session.commit()
        db_session.refresh(chunk)

        with patch(
            "app.ai.rag.embeddings.embed_query",
            return_value=[0.1] * 1536,
        ), patch(
            "app.ai.rag.retrieval.search_chunks",
            return_value=[(chunk, 0.1)],
        ), patch(
            "app.ai.rag._generate_answer",
            return_value="You can get a refund within 30 days.",
        ):
            result = rag.answer_question(
                db_session, chatbot, "Refund policy?"
            )

        assert result.used_fallback is False
        assert "refund" in result.answer.lower()
        assert len(result.sources) == 1
        assert result.sources[0]["title"] == "FAQ"
