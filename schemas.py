"""
Database Schemas for Mountain Gear Rental App

Each Pydantic model represents a MongoDB collection. Collection name is the
lowercase of the class name (e.g., Gear -> "gear").
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    is_active: bool = Field(True, description="Whether user is active")

class Gear(BaseModel):
    title: str = Field(..., description="Gear name")
    description: Optional[str] = Field(None, description="Gear description")
    price_per_day: float = Field(..., ge=0, description="Rental price per day")
    category: str = Field(..., description="Category: tenda, tracking pole, sleeping bag, kompor, carrier, dll")
    image_url: Optional[str] = Field(None, description="Image URL")
    stock: int = Field(1, ge=0, description="Available stock")
    rating: Optional[float] = Field(4.8, ge=0, le=5)

class TransactionItem(BaseModel):
    gear_id: str
    quantity: int = Field(1, ge=1)
    days: int = Field(1, ge=1)

class Transaction(BaseModel):
    user_id: str
    items: List[TransactionItem]
    total_amount: float
    status: str = Field("pending", description="pending | paid | cancelled")

class Message(BaseModel):
    user_id: str
    content: str
    is_read: bool = False

# Backward-compat example:
class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
