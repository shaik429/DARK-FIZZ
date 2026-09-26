from fastapi import FastAPI
from app.database import engine

app = FastAPI()

@app.get("/test-db")
def test_db():
    try:
        conn = engine.connect()
        conn.close()
        return {"status": "Database connected successfully!"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}