
from tests.test_memberships import (
    auth,
    create_org,
    login,
    register,
)


def make_chatbot(client, token, org_id, name="Support Bot"):
    return client.post(
        f"/api/v1/organizations/{org_id}/chatbots",
        json={"name": name},
        headers=auth(token),
    )


class TestChatbotCrud:
    def test_create_chatbot(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        response = make_chatbot(client, token, org_id)
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Support Bot"
        assert body["is_active"] is True
        assert body["public_widget_id"]
        # Widget ID must be long and unguessable, not a sequential int.
        assert len(body["public_widget_id"]) >= 20

    def test_widget_ids_are_unique(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        first = make_chatbot(client, token, org_id).json()
        second = make_chatbot(client, token, org_id, "Bot 2").json()
        assert first["public_widget_id"] != second["public_widget_id"]

    def test_list_chatbots(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        make_chatbot(client, token, org_id)

        response = client.get(
            f"/api/v1/organizations/{org_id}/chatbots", headers=auth(token)
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_update_chatbot(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        bot = make_chatbot(client, token, org_id).json()

        response = client.patch(
            f"/api/v1/organizations/{org_id}/chatbots/{bot['id']}",
            json={
                "welcome_message": "Hi! How can I help?",
                "allowed_domains": ["example.com"],
                "branding": {"primary_color": "#4f46e5"},
            },
            headers=auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["welcome_message"] == "Hi! How can I help?"
        assert body["allowed_domains"] == ["example.com"]
        assert body["branding"]["primary_color"] == "#4f46e5"
        # Widget ID must not change on update.
        assert body["public_widget_id"] == bot["public_widget_id"]

    def test_deactivate_chatbot(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        bot = make_chatbot(client, token, org_id).json()

        response = client.patch(
            f"/api/v1/organizations/{org_id}/chatbots/{bot['id']}",
            json={"is_active": False},
            headers=auth(token),
        )
        assert response.json()["is_active"] is False

    def test_delete_chatbot(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)
        bot = make_chatbot(client, token, org_id).json()

        response = client.delete(
            f"/api/v1/organizations/{org_id}/chatbots/{bot['id']}",
            headers=auth(token),
        )
        assert response.status_code == 204

        response = client.get(
            f"/api/v1/organizations/{org_id}/chatbots/{bot['id']}",
            headers=auth(token),
        )
        assert response.status_code == 404

    def test_get_nonexistent_chatbot(self, client):
        register(client, "a@example.com")
        token = login(client, "a@example.com")
        org_id = create_org(client, token)

        response = client.get(
            f"/api/v1/organizations/{org_id}/chatbots/999", headers=auth(token)
        )
        assert response.status_code == 404


class TestChatbotTenantIsolation:
    def test_non_member_gets_404(self, client):
        register(client, "owner@example.com")
        owner_token = login(client, "owner@example.com")
        org_id = create_org(client, owner_token)
        make_chatbot(client, owner_token, org_id)

        register(client, "outsider@example.com")
        outsider = login(client, "outsider@example.com")

        response = client.get(
            f"/api/v1/organizations/{org_id}/chatbots", headers=auth(outsider)
        )
        assert response.status_code == 404

        response = make_chatbot(client, outsider, org_id)
        assert response.status_code == 404

    def test_cannot_access_other_orgs_chatbot(self, client):
        register(client, "a@example.com")
        token_a = login(client, "a@example.com")
        org_a = create_org(client, token_a, "Org A")
        bot = make_chatbot(client, token_a, org_a).json()

        register(client, "b@example.com")
        token_b = login(client, "b@example.com")
        org_b = create_org(client, token_b, "Org B")

        # Bot id from org A requested under org B -> 404.
        response = client.get(
            f"/api/v1/organizations/{org_b}/chatbots/{bot['id']}",
            headers=auth(token_b),
        )
        assert response.status_code == 404

        # Org B cannot see org A's bot even by listing.
        response = client.get(
            f"/api/v1/organizations/{org_b}/chatbots", headers=auth(token_b)
        )
        assert response.json() == []

    def test_requires_auth(self, client):
        response = client.get("/api/v1/organizations/1/chatbots")
        assert response.status_code == 401
