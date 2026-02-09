import sys
import os

# Add parent directory to sys.path to allow running from backend/ directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import Base, engine


from backend.auth.routes import router as auth_router
from backend.api.query import router as query_router
from backend.api.ingest import router as ingest_router
from backend.api.admin import router as admin_router
from backend.api.chat import router as chat_router
from backend.api.feedback import router as feedback_router
from backend.api.whatsapp import router as whatsapp_router
from backend.api.placement import router as placement_router


# ✅ CREATE APP ONCE
app = FastAPI(title=settings.APP_NAME)

# ✅ CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Create DB tables
Base.metadata.create_all(bind=engine)

# ✅ Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(query_router, prefix="/api", tags=["Query"])
app.include_router(ingest_router, prefix="/api", tags=["Ingest"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(feedback_router, prefix="/api", tags=["Feedback"])
app.include_router(whatsapp_router, prefix="/api", tags=["WhatsApp"])
app.include_router(placement_router, prefix="/api/placements", tags=["Placements"])


@app.get("/")
@app.get("/health")
def root():
    return {"status": "ok", "message": "College Admission Agent is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
