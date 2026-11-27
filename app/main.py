
from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.chatbots.router import router as chatbots_router
from app.faqs.router import router as faqs_router
from app.knowledge.router import router as knowledge_router
from app.memberships.router import router as memberships_router
from app.organizations.router import router as organizations_router


app = FastAPI(
    title="Jhinku AI",
    description="AI Customer Support SaaS Platform",
    version="0.1.0"
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
