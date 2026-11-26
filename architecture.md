# Jhinku AI — System Architecture

**Project:** Jhinku AI  
**Type:** Multi-Tenant AI Customer Support SaaS  
**Architecture:** Modular Monolith (initially)  
**Backend:** Python + FastAPI  
**Database:** PostgreSQL + pgvector  
**Frontend:** Next.js + TypeScript  
**AI Architecture:** Retrieval-Augmented Generation (RAG)

---

# 1. Project Overview

Jhinku AI is a multi-tenant AI-powered customer support SaaS platform.

It allows businesses to create their own AI customer support chatbot using their company knowledge base.

Businesses can upload FAQs, PDF files, documents, and other knowledge sources. Jhinku AI processes these documents, creates embeddings, and stores them in a vector database.

Customers can interact with the AI chatbot through an embeddable website chat widget.

The AI retrieves relevant information from the specific business's knowledge base and generates context-aware answers.

If the AI cannot confidently answer a question, it should offer human support or create a human handoff request.

## Main Goal

Build a production-ready SaaS platform where multiple businesses can independently manage their:

- Organizations
- Team members
- AI chatbots
- Knowledge bases
- FAQs
- Documents
- Conversations
- Human support agents
- Chat widget settings
- Usage and subscription plans

Each organization must have isolated data.

---

# 2. Core Product Features

## 2.1 Organization Management

- Organization registration
- Organization profile
- Organization settings
- Organization members
- Multiple roles and permissions
- Organization-specific data isolation

## 2.2 Authentication and Authorization

- User registration
- Login and logout
- JWT access tokens
- Refresh token rotation
- Secure password hashing
- Forgot password
- Email verification
- Role-based access control (RBAC)

Roles:

- Owner
- Admin
- Agent
- Member

A user may belong to multiple organizations.

## 2.3 AI Chatbot Management

Each organization can create and manage its own chatbot.

Features:

- Create chatbot
- Update chatbot
- Delete chatbot
- Chatbot name
- Chatbot welcome message
- Chatbot system instructions
- AI model configuration
- Chatbot status
- Widget configuration
- Brand colors and customization

## 2.4 Knowledge Base Management

Organizations can provide knowledge through:

- FAQs
- PDF documents
- TXT files
- DOCX files
- Website URLs (future feature)

Features:

- Upload documents
- Extract text
- Clean text
- Split text into chunks
- Generate embeddings
- Store embeddings in PostgreSQL using pgvector
- Search relevant chunks
- Update and delete knowledge sources
- Track document processing status

## 2.5 RAG Engine

The AI must answer using the organization's own knowledge base.

RAG workflow:

1. Customer submits a question.
2. Backend identifies the requested chatbot and its organization.
3. Backend validates the public widget identifier and allowed website domain.
4. Backend converts the question into an embedding.
5. Vector search retrieves relevant chunks.
6. Retrieval is filtered by organization and chatbot/knowledge scope.
7. Relevant chunks are passed to the LLM as context.
8. LLM generates an answer.
9. Backend returns the answer and relevant source references.
10. If relevant information is insufficient, the AI must not invent an answer; it should use a configured fallback or offer human support.

Never allow one organization's documents or embeddings to appear in another organization's retrieval results.

## 2.6 Embeddable Chat Widget

Businesses should be able to embed the chatbot on their websites.

Example:

```html
<script
  src="https://your-domain.com/widget.js"
  data-chatbot-id="PUBLIC_CHATBOT_ID"
  async
></script>
```

Widget features:

- Floating chat button
- Chat window
- Welcome message
- Message history
- Typing indicator
- Streaming responses
- Responsive design
- Loading states
- Error handling
- Human handoff option
- Custom branding

Security:

- Never expose private API keys in the browser.
- Public chatbot/widget ID is not an authentication secret.
- Validate the website domain on the backend.
- Apply rate limiting and abuse protection.
- Do not trust organization IDs supplied by the public client.

## 2.7 Human Support System

When the AI cannot solve a question, the customer can request human support.

Features:

- Human handoff
- Agent inbox
- Conversation assignment
- Conversation status
- Agent replies
- Conversation history
- Internal notes
- Typing indicator
- Real-time updates

## 2.8 Analytics and Usage Tracking

Track:

- Total conversations
- Total messages
- AI responses
- Human handoffs
- Token usage
- LLM API costs
- Knowledge base usage
- Organization usage limits

## 2.9 Subscription and Billing

Initial implementation:

- Free plan
- Usage limits
- Message limits
- Chatbot limits
- Document storage limits

Payment gateway integration can be added later.

---

# 3. Technology Stack

## Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- pgvector
- JWT authentication
- Argon2 or bcrypt password hashing

## AI / RAG

- OpenAI API or Gemini API
- Embeddings API
- PostgreSQL + pgvector
- Direct Python SDK initially
- LangChain optional later

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Query or TanStack Query

## Chat Widget

- React
- TypeScript
- Lightweight embeddable JavaScript bundle

## Infrastructure

- Docker
- Redis
- Celery or another background job worker
- GitHub Actions
- Cloud deployment
- Logging and monitoring

---

# 4. High-Level System Architecture

```text
                       CUSTOMERS
                           |
                           v
                  EMBEDDABLE CHAT WIDGET
                           |
                           v
                    FASTAPI BACKEND
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
       Authentication   Chat API     Knowledge API
             |             |             |
             v             v             v
        Organization    RAG ENGINE    Document Pipeline
        & Membership        |             |
             |              v             v
             |        Embedding API   Text Extraction
             |              |             |
             +--------------+-------------+
                            |
                            v
                      POSTGRESQL
                         + pgvector
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
          Users        Organizations   Knowledge Chunks
                            |
                            v
                       Conversations
                            |
                            v
                      Human Support
                            |
                            v
                       Agent Inbox
```

---

# 5. Backend Architecture

Use a modular monolith initially.

Do not introduce microservices until there is a genuine scaling requirement.

Recommended backend structure:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── migrations/
│   │
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   ├── users/
│   │   ├── organizations/
│   │   ├── memberships/
│   │   ├── chatbots/
│   │   ├── faqs/
│   │   ├── knowledge/
│   │   ├── documents/
│   │   ├── embeddings/
│   │   ├── conversations/
│   │   ├── messages/
│   │   ├── human_support/
│   │   ├── analytics/
│   │   └── billing/
│   │
│   ├── ai/
│   │   ├── providers/
│   │   ├── embeddings.py
│   │   ├── retrieval.py
│   │   ├── rag.py
│   │   ├── prompts.py
│   │   └── guardrails.py
│   │
│   ├── workers/
│   │   └── document_tasks.py
│   │
│   └── shared/
│       ├── pagination.py
│       └── utilities.py
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
├── Dockerfile
└── README.md
```

Each module should follow a consistent structure:

- `models.py`: SQLAlchemy database models
- `schemas.py`: Pydantic request and response schemas
- `service.py`: Business logic
- `router.py`: FastAPI endpoints

Keep database operations and business logic out of route handlers as the project grows.

---

# 6. Database Architecture

Core entities:

## Users

- id
- name
- email
- password_hash
- is_active
- email_verified
- created_at

## Organizations

- id
- name
- slug
- created_at

## Organization Memberships

- id
- user_id
- organization_id
- role
- created_at

## Chatbots

- id
- organization_id
- name
- public_widget_id
- system_prompt
- welcome_message
- is_active
- created_at

## FAQs

- id
- organization_id
- chatbot_id (nullable if shared organization-level FAQ design is selected)
- question
- answer
- created_at
- updated_at

## Knowledge Sources

- id
- organization_id
- chatbot_id
- source_type
- title
- file_path
- processing_status
- created_at

## Knowledge Chunks

- id
- organization_id
- chatbot_id
- knowledge_source_id
- content
- embedding
- chunk_index
- metadata

## Conversations

- id
- organization_id
- chatbot_id
- customer_identifier
- status
- assigned_agent_id
- created_at
- updated_at

## Messages

- id
- conversation_id
- sender_type
- content
- metadata
- created_at

## Usage Records

- id
- organization_id
- metric
- quantity
- recorded_at

## Relationships

- User ↔ Organization: Many-to-Many through Organization Memberships
- Organization → Chatbots: One-to-Many
- Organization → FAQs: One-to-Many
- Organization → Knowledge Sources: One-to-Many
- Knowledge Source → Knowledge Chunks: One-to-Many
- Organization → Conversations: One-to-Many
- Conversation → Messages: One-to-Many
- Organization → Usage Records: One-to-Many

All organization-owned records must be scoped by organization_id.

Use database constraints and indexes where appropriate.

Use PostgreSQL pgvector for embedding storage and vector similarity search.

---

# 7. Multi-Tenancy and Security

Multi-tenancy is a core architectural requirement.

Every authenticated organization request must verify that the logged-in user belongs to the requested organization.

Never trust organization_id from the frontend without authorization checks.

Required security rules:

1. Validate organization membership on every protected organization request.
2. Apply organization filters to all organization-owned queries.
3. Verify ownership on GET, PUT, PATCH and DELETE.
4. Filter vector search by organization_id and chatbot/knowledge scope.
5. Never expose private LLM API keys to the widget.
6. Hash passwords securely.
7. Use short-lived JWT access tokens.
8. Implement refresh token rotation and revocation.
9. Validate uploaded file types and sizes.
10. Apply rate limiting to public endpoints.
11. Validate widget website domains.
12. Keep secrets in environment variables.
13. Avoid leaking sensitive details in error messages.

Consider PostgreSQL Row-Level Security as an additional defense-in-depth measure after application-level tenant authorization is implemented.

---

# 8. API Architecture

Use versioned routes:

```text
/api/v1/
```

## Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

## Organizations

```text
POST   /api/v1/organizations
GET    /api/v1/organizations
GET    /api/v1/organizations/{organization_id}
PATCH  /api/v1/organizations/{organization_id}
DELETE /api/v1/organizations/{organization_id}
```

## Memberships

```text
POST   /api/v1/organizations/{organization_id}/members
GET    /api/v1/organizations/{organization_id}/members
PATCH  /api/v1/organizations/{organization_id}/members/{member_id}
DELETE /api/v1/organizations/{organization_id}/members/{member_id}
```

## Chatbots

```text
POST   /api/v1/organizations/{organization_id}/chatbots
GET    /api/v1/organizations/{organization_id}/chatbots
GET    /api/v1/organizations/{organization_id}/chatbots/{chatbot_id}
PATCH  /api/v1/organizations/{organization_id}/chatbots/{chatbot_id}
DELETE /api/v1/organizations/{organization_id}/chatbots/{chatbot_id}
```

## FAQs

```text
POST   /api/v1/organizations/{organization_id}/faqs
GET    /api/v1/organizations/{organization_id}/faqs
GET    /api/v1/organizations/{organization_id}/faqs/{faq_id}
PUT    /api/v1/organizations/{organization_id}/faqs/{faq_id}
PATCH  /api/v1/organizations/{organization_id}/faqs/{faq_id}
DELETE /api/v1/organizations/{organization_id}/faqs/{faq_id}
```

## Knowledge Base

```text
POST   /api/v1/organizations/{organization_id}/knowledge-sources
GET    /api/v1/organizations/{organization_id}/knowledge-sources
GET    /api/v1/organizations/{organization_id}/knowledge-sources/{source_id}
DELETE /api/v1/organizations/{organization_id}/knowledge-sources/{source_id}
```

## Public Chat

```text
GET  /api/v1/public/chatbots/{public_widget_id}
POST /api/v1/public/chatbots/{public_widget_id}/conversations
POST /api/v1/public/conversations/{conversation_id}/messages
GET  /api/v1/public/conversations/{conversation_id}/messages
```

Public endpoints must validate widget identity, origin/domain policy, rate limits and conversation access.

## Human Support

```text
GET   /api/v1/organizations/{organization_id}/conversations
GET   /api/v1/organizations/{organization_id}/conversations/{conversation_id}
PATCH /api/v1/organizations/{organization_id}/conversations/{conversation_id}
POST  /api/v1/organizations/{organization_id}/conversations/{conversation_id}/assign
POST  /api/v1/organizations/{organization_id}/conversations/{conversation_id}/messages
```

---

# 9. RAG Processing Pipeline

Document ingestion:

```text
Document Upload
      |
      v
File Validation
      |
      v
Text Extraction
      |
      v
Text Cleaning
      |
      v
Chunking
      |
      v
Embedding Generation
      |
      v
PostgreSQL + pgvector
```

Question answering:

```text
Customer Question
       |
       v
Widget Validation
       |
       v
Question Embedding
       |
       v
Tenant-Scoped Vector Search
       |
       v
Relevant Context Retrieval
       |
       v
Prompt Construction
       |
       v
LLM Generation
       |
       v
Answer + Sources
       |
       v
Customer
```

Important:

- Start with a simple chunking strategy.
- Store source metadata.
- Use similarity thresholds and retrieval evaluation.
- Do not fabricate answers when relevant context is missing.
- Treat uploaded documents as untrusted content, not as instructions that override system rules.
- Add reranking and advanced retrieval only when needed.

---

# 10. Frontend Architecture

Recommended structure:

```text
frontend/
│
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   │
│   ├── dashboard/
│   │   ├── overview/
│   │   ├── organizations/
│   │   ├── chatbots/
│   │   ├── knowledge-base/
│   │   ├── faqs/
│   │   ├── conversations/
│   │   ├── agents/
│   │   ├── analytics/
│   │   └── settings/
│   │
│   └── layout.tsx
│
├── components/
├── features/
├── hooks/
├── lib/
├── services/
├── types/
└── public/
```

Dashboard features:

- Organization overview
- Chatbot management
- FAQ management
- Knowledge base uploads
- Conversation inbox
- Agent management
- Usage analytics
- Widget customization
- Account settings

---

# 11. Background Processing

Document processing and embedding generation should not block normal API requests.

Use:

- Redis
- Celery or another background job system

Example:

```text
Upload Request
      |
      v
FastAPI
      |
      v
Save Document Metadata
      |
      v
Queue Background Task
      |
      v
Worker
      |
      v
Extract + Chunk + Embed
      |
      v
Update Processing Status
```

Start with synchronous processing for a small prototype if necessary, then introduce background workers before production-scale document ingestion.

---

# 12. Testing Strategy

Backend tests:

- Authentication tests
- Organization authorization tests
- FAQ CRUD tests
- Membership tests
- Tenant isolation tests
- File upload validation tests
- RAG retrieval tests
- Public widget security tests

Critical multi-tenant test:

1. Create Organization A.
2. Create Organization B.
3. Add separate FAQs and documents.
4. Authenticate as a member of Organization A.
5. Attempt to read or modify Organization B's resources.
6. Verify that access is denied.
7. Verify vector search never returns Organization B's content.

Use isolated test databases and test fixtures.

---

# 13. Development Roadmap

## Phase 1 — Backend Fundamentals

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic
- CRUD APIs

## Phase 2 — SaaS Foundation

- User registration
- Login
- JWT authentication
- Password hashing
- Organizations
- Memberships
- Roles and permissions
- Tenant isolation

## Phase 3 — Chatbot Management

- Create chatbot
- Update chatbot
- Chatbot configuration
- Public widget ID
- Widget domain allowlist

## Phase 4 — Knowledge Base

- FAQ management
- PDF/TXT/DOCX upload
- Text extraction
- Chunking
- Embeddings
- pgvector

## Phase 5 — AI RAG Engine

- Semantic search
- Context retrieval
- Prompt construction
- LLM integration
- Answer generation
- Source citations
- Fallback behavior

## Phase 6 — Frontend and Widget

- Next.js dashboard
- Authentication UI
- Knowledge base UI
- Chatbot settings
- Embeddable widget
- Streaming responses

## Phase 7 — Human Support

- Agent inbox
- Conversation assignment
- Human handoff
- Real-time messaging

## Phase 8 — Production

- Redis
- Background workers
- Rate limiting
- Monitoring
- Docker
- CI/CD
- Deployment
- Usage limits
- Billing

---

# 14. Engineering Principles

1. Build a modular monolith first.
2. Keep code maintainable and testable.
3. Use service layers for business logic.
4. Keep API routes thin.
5. Use SQLAlchemy ORM and Alembic migrations.
6. Never modify production database schemas manually without migrations.
7. Do not hardcode secrets.
8. Use environment-based configuration.
9. Enforce tenant isolation at the backend.
10. Write tests for critical functionality.
11. Avoid unnecessary dependencies.
12. Do not introduce AI complexity before the basic backend foundation is reliable.

---

# 15. Current Development Status

Already implemented or completed:

- FastAPI project setup
- PostgreSQL connection
- SQLAlchemy engine and session
- FAQ SQLAlchemy model
- Alembic initialization
- Initial FAQ table migration
- Organization SQLAlchemy model
- Organization-to-FAQ relationship
- Organization migration
- Organization CRUD: create and read
- Organization-scoped FAQ CRUD
- Organization-scoped FAQ lookup and updates

Current development environment:

- Windows
- Backend directory: `D:\jhinku-ai\backend`
- PostgreSQL database: `jhinku_ai_db`
- Database GUI: Beekeeper Studio
- Python virtual environment: `backend/venv`

Important implementation status:

- Authentication is not implemented yet.
- Organization membership and RBAC are not implemented yet.
- Organization IDs in the current development endpoints are not yet protected by authenticated membership checks.
- RAG and embeddings are not implemented yet.
- Frontend and chat widget are not implemented yet.

The existing project must be extended incrementally. Do not discard working code or rewrite the entire backend unnecessarily.

---

# Final Product Vision

Jhinku AI should become a complete multi-tenant AI customer support platform.

A business should be able to:

1. Register and create an organization.
2. Invite team members.
3. Create an AI chatbot.
4. Upload company FAQs and documents.
5. Configure chatbot appearance and behavior.
6. Embed the chatbot into its website.
7. Let customers ask questions.
8. Receive answers based on its own knowledge base.
9. Transfer difficult conversations to human agents.
10. Monitor usage, conversations and performance.

The platform must be secure, scalable, maintainable, cost-conscious and suitable for real businesses.