
from tests.test_memberships import (
    auth,
    create_org,
    login,
    register,
)


def _setup(client):
    """Owner + org + chatbot + one public conversation with a message."""
    register(client, "owner@example.com")
    owner = login(client, "owner@example.com")
    org_id = create_org(client, owner)
    bot = client.post(
        f"/api/v1/organizations/{org_id}/chatbots",
        json={"name": "Bot"},
        headers=auth(owner),
    ).json()
    conv = client.post(
        f"/api/v1/public/chatbots/{bot['public_widget_id']}/conversations",
        json={"customer_identifier": "visitor-1"},
    ).json()
    return owner, org_id, bot, conv


def _conv_id(client, owner, org_id):
    convs = client.get(
        f"/api/v1/organizations/{org_id}/conversations",
        headers=auth(owner),
    ).json()
    return convs[0]["id"]


class TestAgentInbox:
    def test_list_conversations(self, client):
        owner, org_id, bot, conv = _setup(client)
        response = client.get(
            f"/api/v1/organizations/{org_id}/conversations",
            headers=auth(owner),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["customer_identifier"] == "visitor-1"
        assert data[0]["status"] == "active"

    def test_filter_by_status(self, client):
        owner, org_id, bot, conv = _setup(client)
        response = client.get(
            f"/api/v1/organizations/{org_id}/conversations",
            params={"status": "closed"},
            headers=auth(owner),
        )
        assert response.json() == []

    def test_get_conversation_detail(self, client):
        owner, org_id, bot, conv = _setup(client)
        cid = _conv_id(client, owner, org_id)
        response = client.get(
            f"/api/v1/organizations/{org_id}/conversations/{cid}",
            headers=auth(owner),
        )
        assert response.status_code == 200
        assert "messages" in response.json()

    def test_non_member_gets_404(self, client):
        owner, org_id, bot, conv = _setup(client)
        register(client, "outsider@example.com")
        outsider = login(client, "outsider@example.com")
        response = client.get(
            f"/api/v1/organizations/{org_id}/conversations",
            headers=auth(outsider),
        )
        assert response.status_code == 404


class TestAgentActions:
    def test_agent_reply_marks_human(self, client):
        owner, org_id, bot, conv = _setup(client)
        cid = _conv_id(client, owner, org_id)

        response = client.post(
            f"/api/v1/organizations/{org_id}/conversations/{cid}/messages",
            json={"content": "Hi, how can I help?"},
            headers=auth(owner),
        )
        assert response.status_code == 201
        assert response.json()["sender_type"] == "agent"

        convs = client.get(
            f"/api/v1/organizations/{org_id}/conversations",
            headers=auth(owner),
        ).json()
        assert convs[0]["status"] == "human"
        assert convs[0]["assigned_agent_id"] is not None

    def test_internal_note_hidden_from_customer(self, client):
        owner, org_id, bot, conv = _setup(client)
        cid = _conv_id(client, owner, org_id)

        client.post(
            f"/api/v1/organizations/{org_id}/conversations/{cid}/messages",
            json={"content": "SECRET: customer is angry", "is_internal": True},
            headers=auth(owner),
        )

        # Agent detail sees the note.
        detail = client.get(
            f"/api/v1/organizations/{org_id}/conversations/{cid}",
            headers=auth(owner),
        ).json()
        assert any(m["is_internal"] for m in detail["messages"])

        # Public history must NOT include it.
        public = client.get(
            f"/api/v1/public/conversations/{conv['public_id']}/messages",
            params={"customer_identifier": "visitor-1"},
        ).json()
        assert all(not m.get("metadata") or True for m in public)
        assert "SECRET" not in str(public)

    def test_assign_agent(self, client):
        owner, org_id, bot, conv = _setup(client)
        cid = _conv_id(client, owner, org_id)

        response = client.post(
            f"/api/v1/organizations/{org_id}/conversations/{cid}/assign",
            json={},
            headers=auth(owner),
        )
        assert response.status_code == 200
        assert response.json()["assigned_agent_id"] is not None
        assert response.json()["status"] == "human"

    def test_update_status(self, client):
        owner, org_id, bot, conv = _setup(client)
        cid = _conv_id(client, owner, org_id)
        response = client.patch(
            f"/api/v1/organizations/{org_id}/conversations/{cid}",
            json={"status": "closed"},
            headers=auth(owner),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "closed"


class TestHandoff:
    def test_customer_requests_human(self, client):
        owner, org_id, bot, conv = _setup(client)

        response = client.post(
            f"/api/v1/public/conversations/{conv['public_id']}/handoff",
            json={"customer_identifier": "visitor-1"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "waiting_human"

        # Agent inbox shows it as waiting_human.
        convs = client.get(
            f"/api/v1/organizations/{org_id}/conversations",
            params={"status": "waiting_human"},
            headers=auth(owner),
        ).json()
        assert len(convs) == 1

        # A system message was recorded.
        cid = convs[0]["id"]
        detail = client.get(
            f"/api/v1/organizations/{org_id}/conversations/{cid}",
            headers=auth(owner),
        ).json()
        assert any(m["sender_type"] == "system" for m in detail["messages"])

    def test_handoff_wrong_customer_404(self, client):
        owner, org_id, bot, conv = _setup(client)
        response = client.post(
            f"/api/v1/public/conversations/{conv['public_id']}/handoff",
            json={"customer_identifier": "impostor"},
        )
        assert response.status_code == 404
