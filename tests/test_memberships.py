
import pytest


def register(client, email, password="password123"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )


def login(client, email, password="password123"):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_org(client, token, name="Acme Corp"):
    response = client.post(
        "/api/v1/organizations", json={"name": name}, headers=auth(token)
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture()
def owner(client):
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    org_id = create_org(client, token)
    return token, org_id


@pytest.fixture()
def member(client):
    register(client, "member@example.com")
    return login(client, "member@example.com")


class TestOrganizationAccess:
    def test_create_org_requires_auth(self, client):
        response = client.post(
            "/api/v1/organizations", json={"name": "No Auth Org"}
        )
        assert response.status_code == 401

    def test_creator_becomes_owner(self, client, owner):
        token, org_id = owner
        orgs = client.get("/api/v1/organizations", headers=auth(token))
        assert orgs.status_code == 200
        data = orgs.json()
        assert len(data) == 1
        assert data[0]["id"] == org_id
        assert data[0]["role"] == "owner"

    def test_list_orgs_only_shows_member_orgs(self, client, owner, member):
        token, _ = owner
        # Member has no orgs yet.
        response = client.get("/api/v1/organizations", headers=auth(member))
        assert response.json() == []

        # Owner's org is invisible to a non-member.
        create_org(client, member, "Member Org")
        member_orgs = client.get(
            "/api/v1/organizations", headers=auth(member)
        ).json()
        owner_orgs = client.get(
            "/api/v1/organizations", headers=auth(token)
        ).json()
        assert len(member_orgs) == 1
        assert len(owner_orgs) == 1
        assert member_orgs[0]["id"] != owner_orgs[0]["id"]

    def test_non_member_gets_404_on_org(self, client, owner, member):
        _, org_id = owner
        response = client.get(
            f"/api/v1/organizations/{org_id}", headers=auth(member)
        )
        assert response.status_code == 404


class TestMemberManagement:
    def test_add_and_list_members(self, client, owner, member):
        token, org_id = owner

        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "member@example.com", "role": "member"},
            headers=auth(token),
        )
        assert response.status_code == 201
        assert response.json()["role"] == "member"

        members = client.get(
            f"/api/v1/organizations/{org_id}/members", headers=auth(token)
        ).json()
        assert len(members) == 2
        roles = {m["email"]: m["role"] for m in members}
        assert roles["owner@example.com"] == "owner"
        assert roles["member@example.com"] == "member"

    def test_member_cannot_add_members(self, client, owner, member):
        owner_token, org_id = owner
        client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "member@example.com"},
            headers=auth(owner_token),
        )

        register(client, "third@example.com")
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "third@example.com"},
            headers=auth(member),
        )
        assert response.status_code == 403

    def test_add_unknown_email_fails(self, client, owner):
        token, org_id = owner
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "ghost@example.com"},
            headers=auth(token),
        )
        assert response.status_code == 404

    def test_duplicate_member_rejected(self, client, owner, member):
        token, org_id = owner
        payload = {"email": "member@example.com"}
        url = f"/api/v1/organizations/{org_id}/members"
        assert client.post(url, json=payload, headers=auth(token)).status_code == 201
        assert client.post(url, json=payload, headers=auth(token)).status_code == 409

    def test_cannot_invite_owner_role(self, client, owner):
        token, org_id = owner
        response = client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "member@example.com", "role": "owner"},
            headers=auth(token),
        )
        assert response.status_code == 400

    def test_change_member_role(self, client, owner, member):
        token, org_id = owner
        client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "member@example.com"},
            headers=auth(token),
        )
        members = client.get(
            f"/api/v1/organizations/{org_id}/members", headers=auth(token)
        ).json()
        member_id = next(m["id"] for m in members if m["email"] == "member@example.com")

        response = client.patch(
            f"/api/v1/organizations/{org_id}/members/{member_id}",
            json={"role": "admin"},
            headers=auth(token),
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_admin_cannot_modify_owner(self, client, owner, member):
        owner_token, org_id = owner
        # Promote member to admin.
        client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "member@example.com", "role": "admin"},
            headers=auth(owner_token),
        )
        members = client.get(
            f"/api/v1/organizations/{org_id}/members", headers=auth(owner_token)
        ).json()
        owner_member_id = next(
            m["id"] for m in members if m["role"] == "owner"
        )

        # Admin tries to demote the owner -> 403.
        response = client.patch(
            f"/api/v1/organizations/{org_id}/members/{owner_member_id}",
            json={"role": "member"},
            headers=auth(member),
        )
        assert response.status_code == 403

    def test_cannot_remove_last_owner(self, client, owner):
        token, org_id = owner
        members = client.get(
            f"/api/v1/organizations/{org_id}/members", headers=auth(token)
        ).json()
        owner_id = members[0]["id"]

        response = client.delete(
            f"/api/v1/organizations/{org_id}/members/{owner_id}",
            headers=auth(token),
        )
        assert response.status_code == 400

    def test_remove_member(self, client, owner, member):
        token, org_id = owner
        client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "member@example.com"},
            headers=auth(token),
        )
        members = client.get(
            f"/api/v1/organizations/{org_id}/members", headers=auth(token)
        ).json()
        member_id = next(m["id"] for m in members if m["email"] == "member@example.com")

        response = client.delete(
            f"/api/v1/organizations/{org_id}/members/{member_id}",
            headers=auth(token),
        )
        assert response.status_code == 204

        # Removed member loses access.
        response = client.get(
            f"/api/v1/organizations/{org_id}", headers=auth(member)
        )
        assert response.status_code == 404


class TestFaqTenantIsolation:
    def _add_faq(self, client, token, org_id):
        return client.post(
            f"/api/v1/organizations/{org_id}/faqs",
            json={"question": "What is Jhinku?", "answer": "An AI support platform."},
            headers=auth(token),
        )

    def test_member_can_crud_faqs(self, client, owner, member):
        owner_token, org_id = owner
        client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "member@example.com"},
            headers=auth(owner_token),
        )

        response = self._add_faq(client, member, org_id)
        assert response.status_code == 201

        faqs = client.get(
            f"/api/v1/organizations/{org_id}/faqs", headers=auth(member)
        ).json()
        assert faqs["total"] == 1

    def test_non_member_cannot_access_faqs(self, client, owner, member):
        _, org_id = owner
        response = client.get(
            f"/api/v1/organizations/{org_id}/faqs", headers=auth(member)
        )
        assert response.status_code == 404

        response = self._add_faq(client, member, org_id)
        assert response.status_code == 404

    def test_faqs_require_auth(self, client, owner):
        _, org_id = owner
        response = client.get(f"/api/v1/organizations/{org_id}/faqs")
        assert response.status_code == 401
