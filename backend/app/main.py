from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.handlers import register_exception_handlers
from app.database import engine
from app.routes import auth, dashboard, master, operations, products

app = FastAPI(title="StockSense API", description="Inventory Management System - Odoo x GCET 2026")

register_exception_handlers(app)  # BEFORE CORS so error responses keep CORS headers

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(master.router)
app.include_router(operations.router)


@app.get("/health", tags=["health"])
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
