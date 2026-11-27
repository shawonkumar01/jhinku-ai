
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.chatbots.router import router as chatbots_router
from app.faqs.router import router as faqs_router
from app.knowledge.router import router as knowledge_router
from app.memberships.router import router as memberships_router
from app.organizations.router import router as organizations_router


WIDGET_PATH = Path(__file__).parent / "static" / "widget.js"

app = FastAPI(
    title="Jhinku AI",
    description="AI Customer Support SaaS Platform",
    version="0.1.0"
)

# The embeddable widget runs on customers' websites (any origin).
# Auth uses Bearer tokens (not cookies), so wide CORS is safe here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


for router in (
    auth_router,
    organizations_router,
    memberships_router,
    chatbots_router,
    faqs_router,
    knowledge_router,
    chat_router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Welcome to Jhinku AI",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/widget.js")
async def widget_js():
    """The embeddable chat widget script.

    Businesses include it with:
      <script src="https://API_DOMAIN/widget.js"
              data-chatbot-id="PUBLIC_WIDGET_ID" async></script>
    """
    return FileResponse(
        WIDGET_PATH,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/demo", include_in_schema=False)
async def widget_demo():
    """Local test page for the widget (not part of the API)."""
    return FileResponse(
        Path(__file__).parent / "static" / "demo.html",
        media_type="text/html",
    )
