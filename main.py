import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Mountain Gear Rental API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

# -------- Schemas (import from schemas.py) --------
from schemas import User, Gear, Transaction, Message, TransactionItem

# --------- Seed helper ---------

def to_public(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Convert nested _id if exist
    return doc

# Backend routes
@app.get("/")
def read_root():
    return {"message": "Mountain Gear Rental API is running"}

@app.get("/test")
def test_database():
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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# -------- Gear endpoints --------
@app.get("/api/gear")
async def list_gear(category: Optional[str] = None, limit: int = 50):
    filt = {"category": category} if category else {}
    items = [to_public(d) for d in get_documents("gear", filt, limit)]
    return {"items": items}

class GearCreate(Gear):
    pass

@app.post("/api/gear")
async def create_gear(payload: GearCreate):
    gear_id = create_document("gear", payload)
    return {"id": gear_id}

# -------- Transactions --------
class TransactionCreate(BaseModel):
    user_id: str
    items: List[TransactionItem]

@app.post("/api/transactions")
async def create_transaction(payload: TransactionCreate):
    # Calculate total
    total = 0.0
    for it in payload.items:
        gear = db["gear"].find_one({"_id": ObjectId(it.gear_id)})
        if not gear:
            raise HTTPException(status_code=404, detail="Gear not found")
        total += float(gear.get("price_per_day", 0)) * it.quantity * it.days
    data = {
        "user_id": payload.user_id,
        "items": [it.model_dump() for it in payload.items],
        "total_amount": total,
        "status": "pending",
    }
    new_id = create_document("transaction", data)
    return {"id": new_id, "total_amount": total, "status": "pending"}

@app.get("/api/transactions")
async def list_transactions(user_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    if status:
        filt["status"] = status
    txs = [to_public(d) for d in get_documents("transaction", filt, limit)]
    return {"items": txs}

# -------- Messages --------
class MessageCreate(BaseModel):
    user_id: str
    content: str

@app.post("/api/messages")
async def create_message(payload: MessageCreate):
    new_id = create_document("message", payload)
    return {"id": new_id}

@app.get("/api/messages")
async def list_messages(user_id: Optional[str] = None, limit: int = 50):
    filt = {"user_id": user_id} if user_id else {}
    msgs = [to_public(d) for d in get_documents("message", filt, limit)]
    return {"items": msgs}

# -------- Users (minimal) --------
class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

@app.post("/api/users")
async def create_user(payload: UserCreate):
    new_id = create_document("user", payload)
    return {"id": new_id}

@app.get("/api/users")
async def list_users(limit: int = 50):
    users = [to_public(d) for d in get_documents("user", {}, limit)]
    return {"items": users}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
