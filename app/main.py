from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import FRONTEND_URL, SESSION_SECRET_KEY
from app.api.routes.auth import router as auth_router
from app.api.routes.profile import router as profile_router
from app.api.routes.agenda import router as agenda_router

from app.api.routes.farms import router as farms_router
from app.api.routes.parcels import router as parcels_router
from app.api.routes.employees import router as employees_router
from app.api.routes.activities import router as activities_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.indices import router as indices_router

from app.api.routes.weather import router as weather_router

print("🔵 Lancement de l'application FastAPI...")

app = FastAPI(
    title="AWAM API",
    version="1.0.0"
)

print("🔵 Ajout du middleware Session...")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

print("🔵 Ajout du middleware CORS...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print(f"🔵 CORS configuré avec FRONTEND_URL = {FRONTEND_URL}")

print("🔵 Ajout du router auth...")
app.include_router(auth_router)

print("🔵 Ajout du router profile...")
app.include_router(profile_router)

print("🔵 Ajout du router agenda...")
app.include_router(agenda_router)

print("🔵 Ajout du router farms...")
app.include_router(farms_router)

print("🔵 Ajout du router parcels...")
app.include_router(parcels_router)

print("🔵 Ajout du router employees...")
app.include_router(employees_router)

print("🔵 Ajout du router activities...")
app.include_router(activities_router)

print("🔵 Ajout du router alerts...")
app.include_router(alerts_router)

print("🔵 Ajout du router indices...")
app.include_router(indices_router)

print("🔵 Ajout du router weather...")
app.include_router(weather_router)



print("✅ Application prête !")


@app.get("/health")
async def health_check():
    return {"status": "ok"}