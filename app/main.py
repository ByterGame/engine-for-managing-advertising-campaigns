from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routers.campaigns import router as campaigns_router
from database.config import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        import rules_engine.rules
        print(f"Правила инициализированны в количестве: {len(rules_engine.rules.__all__)}")
    except ImportError as e:
        print(f"Warning: Правила не импортированы: {e}")
    
    yield
    
    print("Остановка сервиса")
    await engine.dispose()


app = FastAPI(
    title="Campaign Rules Engine Test Task",
    description="API для управления рекламными кампаниями и оценки правил",
    version="0.1.1",
    docs_url="/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(campaigns_router)

@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Campaign Rules Engine Test Task",
        "version": "0.1.1",
        "docs": "/docs",
        "endpoints": {
            "campaigns_crud": "/campaigns",
            "campaign_schedule": "/campaigns/{id}/schedule",
            "evaluate_campaign": "/campaigns/{id}/evaluate",
            "evaluate_all": "/campaigns/evaluate-all",
            "evaluation_history": "/campaigns/{id}/evaluation-history"
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "campaign-rules-engine"}
