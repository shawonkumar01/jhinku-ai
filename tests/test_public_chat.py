
from unittest.mock import patch

from fastapi import Request

from app.ai.rag import RagResult
from app.core import ratelimit
from tests.test_memberships import (
    auth,
    create_org,
    login,
    register,
)


def _setup_chatbot(client, allowed_domains=None):
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    org_id = create_org(client, token)
    payload = {
        "name": "Acme Bot",
        "welcome_message": "Hi! Ask me anything.",
        "allowed_domains": allowed_domains,
    }
    bot = client.post(
        f"/organizations/{org_id}/chatbots",
        json=payload,
        headers=auth(token),
    ).json()
    return bot["public_widget_id"]


def _mock_rag():
    return patch(
        "app.chat.service.rag.answer_question",
        return_value=RagResult(
            answer="Here is your answer.",
            sources=[{"title": "FAQ", "chunk_index": 0}],
        ),
    )


class TestPublicChatbotConfig:
    def test_get_public_config(self, client):
        widget_id = _setup_chatbot(client)
        response = client.get(f"/public/chatbots/{widget_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Acme Bot"
        assert body["welcome_message"] == "Hi! Ask me anything."
        # Must NOT leak organization_id or other internals.
        assert "organization_id" not in body
        assert "id" not in body

    def test_unknown_widget_id_404(self, client):
        response = client.get("/public/chatbots/nonexistent")
        assert response.status_code == 404

    def test_inactive_chatbot_404(self, client):
        widget_id = _setup_chatbot(client)
        owner_token = login(client, "owner@example.com")
        orgs = client.get(
            "/organizations", headers=auth(owner_token)
        ).json()
        org_id = orgs[0]["id"]
        bots = client.get(
            f"/organizations/{org_id}/chatbots",
            headers=auth(owner_token),
        ).json()
        client.patch(
            f"/organizations/{org_id}/chatbots/{bots[0]['id']}",
            json={"is_active": False},
            headers=auth(owner_token),
        )
        response = client.get(f"/public/chatbots/{widget_id}")
        assert response.status_code == 404


class TestDomainAllowlist:
    def test_allowed_domain_accepted(self, client):
        widget_id = _setup_chatbot(client, ["example.com"])
        response = client.get(
            f"/public/chatbots/{widget_id}",
            headers={"Origin": "https://example.com"},
        )
        assert response.status_code == 200

    def test_subdomain_accepted(self, client):
        widget_id = _setup_chatbot(client, ["example.com"])
        response = client.get(
            f"/public/chatbots/{widget_id}",
            headers={"Origin": "https://shop.example.com"},
        )
        assert response.status_code == 200

    def test_disallowed_domain_rejected(self, client):
        widget_id = _setup_chatbot(client, ["example.com"])
        response = client.get(
            f"/public/chatbots/{widget_id}",
            headers={"Origin": "https://evil.com"},
        )
        assert response.status_code == 403

    def test_no_origin_rejected_when_allowlist_set(self, client):
        widget_id = _setup_chatbot(client, ["example.com"])
        response = client.get(f"/public/chatbots/{widget_id}")
        assert response.status_code == 403

    def test_empty_allowlist_allows_any(self, client):
        widget_id = _setup_chatbot(client, None)
        response = client.get(
            f"/public/chatbots/{widget_id}",
            headers={"Origin": "https://anything.com"},
        )
        assert response.status_code == 200


class TestConversations:
    def test_create_conversation(self, client):
        widget_id = _setup_chatbot(client)
        response = client.post(
            f"/public/chatbots/{widget_id}/conversations",
            json={"customer_identifier": "visitor-123"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["public_id"]
        assert body["welcome_message"] == "Hi! Ask me anything."

    def test_send_and_receive_message(self, client):
        widget_id = _setup_chatbot(client)
        conv = client.post(
            f"/public/chatbots/{widget_id}/conversations",
            json={"customer_identifier": "visitor-123"},
        ).json()

        with _mock_rag():
            response = client.post(
                f"/public/conversations/{conv['public_id']}/messages",
                json={
                    "content": "What is your refund policy?",
                    "customer_identifier": "visitor-123",
                },
            )
        assert response.status_code == 200
        body = response.json()
        assert body["sender_type"] == "ai"
        assert body["content"] == "Here is your answer."
        assert body["metadata"]["sources"]

    def test_message_history(self, client):
        widget_id = _setup_chatbot(client)
        conv = client.post(
            f"/public/chatbots/{widget_id}/conversations",
            json={"customer_identifier": "visitor-123"},
        ).json()
        with _mock_rag():
            client.post(
                f"/public/conversations/{conv['public_id']}/messages",
                json={
                    "content": "Hello",
                    "customer_identifier": "visitor-123",
                },
            )

        response = client.get(
            f"/public/conversations/{conv['public_id']}/messages",
            params={"customer_identifier": "visitor-123"},
        )
        assert response.status_code == 200
        messages = response.json()
        # customer + ai
        assert len(messages) == 2
        assert messages[0]["sender_type"] == "customer"
        assert messages[1]["sender_type"] == "ai"

    def test_wrong_customer_identifier_404(self, client):
        widget_id = _setup_chatbot(client)
        conv = client.post(
            f"/public/chatbots/{widget_id}/conversations",
            json={"customer_identifier": "visitor-123"},
        ).json()

        response = client.get(
            f"/public/conversations/{conv['public_id']}/messages",
            params={"customer_identifier": "someone-else"},
        )
        assert response.status_code == 404

    def test_unknown_conversation_404(self, client):
        response = client.post(
            "/public/conversations/fake-id/messages",
            json={"content": "Hi", "customer_identifier": "x"},
        )
        assert response.status_code == 404


class TestRateLimiter:
    def test_allows_requests_under_limit(self):
        ratelimit._hits.clear()
        scope = {
            "type": "http",
            "client": ("1.2.3.4", 1234),
            "headers": [],
        }
        request = Request(scope)
        for _ in range(5):
            ratelimit.rate_limit(request, limit=5, window_seconds=60)

    def test_blocks_over_limit(self):
        ratelimit._hits.clear()
        scope = {
            "type": "http",
            "client": ("5.6.7.8", 1234),
            "headers": [],
        }
        request = Request(scope)
        for _ in range(5):
            ratelimit.rate_limit(request, limit=5, window_seconds=60)
        try:
            ratelimit.rate_limit(request, limit=5, window_seconds=60)
            assert False, "should have raised"
        except Exception as e:
            assert "429" in str(e) or "Too many" in str(e)
        ratelimit._hits.clear()
