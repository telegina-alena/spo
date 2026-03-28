from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    email: EmailStr


class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: int
    email: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ==================== MENU SCHEMAS ====================

class MenuItemCreate(BaseModel):
    """Схема для создания блюда"""
    name: str
    price: float
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class MenuItemResponse(BaseModel):
    """Схема для ответа с данными блюда"""
    id: int
    name: str
    price: float
    category: Optional[str] = None
    description: Optional[str] = None
    is_available: bool
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== CART SCHEMAS ====================

class CartItem(BaseModel):
    """Схема для добавления товара в корзину"""
    menu_item_id: int
    quantity: int = 1


class CartResponse(BaseModel):
    """Схема для ответа с содержимым корзины"""
    id: int
    menu_item_id: int
    name: str
    quantity: int
    price: float
    subtotal: float
    added_at: datetime

    class Config:
        from_attributes = True
