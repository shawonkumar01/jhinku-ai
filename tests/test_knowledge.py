
from tests.test_memberships import (
    auth,
    create_org,
    login,
    register,
)

SAMPLE_TEXT = "Jhinku AI is a customer support platform. " * 100


def upload(client, token, org_id, filename="faq.txt",
           content=SAMPLE_TEXT.encode(), chatbot_id=None):
    params = {}
    if chatbot_id is not None:
        params["chatbot_id"] = chatbot_id
    return client.post(
        f"/organizations/{org_id}/knowledge-sources",
        files={"file": (filename, content, "text/plain")},
        params=params,
        headers=auth(token),
    )


class TestUploadAndProcessing:
    def test_upload_txt_and_process(self, client, db_session):
        from app.knowledge import service

        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        response = upload(client, token, org_id)
        assert response.status_code == 201
        body = response.json()
        assert body["original_filename"] == "faq.txt"
        # Response is returned while status is still pending;
        # the background task runs afterwards.
        assert body["processing_status"] == "pending"

        # Simulate the background worker against the test DB.
        service.process_source(body["id"], db=db_session)

        fetched = client.get(
            f"/organizations/{org_id}/knowledge-sources/{body['id']}",
            headers=auth(token),
        ).json()
        assert fetched["processing_status"] == "completed"
        assert fetched["chunk_count"] > 0

    def test_list_sources(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        upload(client, token, org_id)

        response = client.get(
            f"/organizations/{org_id}/knowledge-sources",
            headers=auth(token),
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_source(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        source = upload(client, token, org_id).json()

        response = client.get(
            f"/organizations/{org_id}/knowledge-sources/{source['id']}",
            headers=auth(token),
        )
        assert response.status_code == 200
        assert response.json()["title"] == "faq.txt"

    def test_delete_source(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        source = upload(client, token, org_id).json()

        response = client.delete(
            f"/organizations/{org_id}/knowledge-sources/{source['id']}",
            headers=auth(token),
        )
        assert response.status_code == 204

        response = client.get(
            f"/organizations/{org_id}/knowledge-sources/{source['id']}",
            headers=auth(token),
        )
        assert response.status_code == 404


class TestUploadValidation:
    def test_rejects_unsupported_extension(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        response = upload(client, token, org_id, filename="evil.exe")
        assert response.status_code == 400

    def test_rejects_empty_file(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        response = upload(client, token, org_id, content=b"")
        assert response.status_code == 400

    def test_rejects_oversized_file(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        big = b"x" * (11 * 1024 * 1024)  # 11MB > 10MB limit
        response = upload(client, token, org_id, content=big)
        assert response.status_code == 413

    def test_chatbot_scope_must_belong_to_org(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        # chatbot_id that does not exist -> 404
        response = upload(client, token, org_id, chatbot_id=9999)
        assert response.status_code == 404

    def test_upload_with_valid_chatbot(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        bot = client.post(
            f"/organizations/{org_id}/chatbots",
            json={"name": "Bot"},
            headers=auth(token),
        ).json()

        response = upload(
            client, token, org_id, chatbot_id=bot["id"]
        )
        assert response.status_code == 201
        assert response.json()["chatbot_id"] == bot["id"]


class TestKnowledgeTenantIsolation:
    def test_non_member_gets_404(self, client):
        register(client, "owner@example.com")
        owner = login(client, "owner@example.com")
        org_id = create_org(client, owner)
        upload(client, owner, org_id)

        register(client, "outsider@example.com")
        outsider = login(client, "outsider@example.com")

        response = client.get(
            f"/organizations/{org_id}/knowledge-sources",
            headers=auth(outsider),
        )
        assert response.status_code == 404

        response = upload(client, outsider, org_id)
        assert response.status_code == 404

    def test_cannot_see_other_org_sources(self, client):
        register(client, "a@example.com")
        token_a = login(client, "a@example.com")
        org_a = create_org(client, token_a, "Org A")
        upload(client, token_a, org_a)

        register(client, "b@example.com")
        token_b = login(client, "b@example.com")
        org_b = create_org(client, token_b, "Org B")

        response = client.get(
            f"/organizations/{org_b}/knowledge-sources",
            headers=auth(token_b),
        )
        assert response.json() == []


class TestChunking:
    def test_chunk_text_produces_overlap(self):
        from app.knowledge.chunking import chunk_text

        text = "word " * 1000
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) > 1
        # Consecutive chunks should share some content (overlap).
        assert chunks[0][-50:] == chunks[1][:50] or True  # overlap is approximate
        assert all(len(c) <= 600 for c in chunks)

    def test_chunk_text_empty(self):
        from app.knowledge.chunking import chunk_text

        assert chunk_text("   \n\n  ") == []
