import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Cat

app = FastAPI(title="Cat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# API models
class LikeResponse(BaseModel):
    likes: int

# Cat endpoints
@app.get("/api/cats")
def list_cats():
    try:
        cats = get_documents("cat", {}, limit=50)
        # Convert ObjectId to string
        for c in cats:
            c["_id"] = str(c["_id"]) if isinstance(c.get("_id"), ObjectId) else c.get("_id")
        return cats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cats")
def create_cat(cat: Cat):
    try:
        cat_id = create_document("cat", cat)
        return {"id": cat_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cats/{cat_id}/like", response_model=LikeResponse)
def like_cat(cat_id: str):
    try:
        from datetime import datetime, timezone
        from bson import ObjectId
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        result = db.cat.find_one_and_update(
            {"_id": ObjectId(cat_id)},
            {"$inc": {"likes": 1}, "$set": {"updated_at": datetime.now(timezone.utc)}},
            return_document=True
        )
        if not result:
            raise HTTPException(status_code=404, detail="Cat not found")
        return LikeResponse(likes=int(result.get("likes", 0)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
