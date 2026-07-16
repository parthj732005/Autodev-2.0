from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, projects
from app.routes import generate, settings_route

app = FastAPI(title="AutoDev 2.0", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/generate", tags=["Generate"])
app.include_router(settings_route.router, prefix="/settings", tags=["Settings"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
