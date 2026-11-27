

def test_widget_js_served(client):
    response = client.get("/widget.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]
    body = response.text
    assert "data-chatbot-id" in body
    assert "/api/v1" in body


def test_demo_page_served(client):
    response = client.get("/demo")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_cors_header_present(client):
    response = client.get(
        "/widget.js", headers={"Origin": "https://customer-site.com"}
    )
    assert response.headers.get("access-control-allow-origin") == "*"
