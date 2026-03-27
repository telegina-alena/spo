import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Optional
import sqlite3
from contextlib import contextmanager

from backend.models.models import (
    UserCreate,
    UserResponse,
    MenuItemCreate,
    MenuItemResponse,
    CartItem,
    CartResponse
)
from database.database import FoodDeliveryDB

app = FastAPI(title="Food Delivery API")

# Создаем глобальный экземпляр БД
db = FoodDeliveryDB("delivery.db")


# ==================== USERS ====================

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    """Создание пользователя"""
    user_id = db.add_user(user.email)
    if not user_id:
        raise HTTPException(status_code=400, detail="Email already exists")
    return db.get_user(user_id=user_id)


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """Получить пользователя по ID"""
    user = db.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ==================== MENU ====================

@app.post("/menu/", response_model=MenuItemResponse)
def create_menu_item(item: MenuItemCreate):
    """Добавить блюдо в меню"""
    item_id = db.add_menu_item(
        name=item.name,
        price=item.price,
        category=item.category,
        description=item.description,
        image_url=item.image_url
    )
    return db.get_menu_item(item_id)


@app.get("/menu/", response_model=List[MenuItemResponse])
def get_menu(category: Optional[str] = None):
    """Получить меню"""
    menu = db.get_menu(category=category)
    if menu is None:
        return []  # возвращаем пустой список вместо None
    return menu


@app.get("/menu/{item_id}", response_model=MenuItemResponse)
def get_menu_item(item_id: int):
    """Получить блюдо по ID"""
    item = db.get_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.patch("/menu/{item_id}")
def update_menu_item(item_id: int, is_available: Optional[bool] = None, price: Optional[float] = None):
    """Обновить блюдо"""
    updates = {}
    if is_available is not None:
        updates['is_available'] = is_available
    if price is not None:
        updates['price'] = price

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if db.update_menu_item(item_id, **updates):
        return {"message": "Menu item updated"}
    raise HTTPException(status_code=404, detail="Item not found")


# ==================== CART ====================

@app.post("/cart/{user_id}/add")
def add_to_cart(user_id: int, item: CartItem):
    """Добавить товар в корзину"""
    user = db.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    menu_item = db.get_menu_item(item.menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if db.add_to_cart(user_id, item.menu_item_id, item.quantity):
        return {"message": "Item added to cart"}
    raise HTTPException(status_code=400, detail="Failed to add to cart")


@app.get("/cart/{user_id}", response_model=List[CartResponse])
def get_cart(user_id: int):
    """Получить корзину"""
    cart = db.get_cart(user_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@app.get("/cart/{user_id}/total")
def get_cart_total(user_id: int):
    """Получить сумму корзины"""
    total = db.get_cart_total(user_id)
    return {"total": total}


@app.delete("/cart/{user_id}/clear")
def clear_cart(user_id: int):
    """Очистить корзину"""
    db.clear_cart(user_id)
    return {"message": "Cart cleared"}


@app.delete("/cart/item/{cart_id}")
def remove_cart_item(cart_id: int):
    """Удалить товар из корзины"""
    if db.remove_from_cart(cart_id):
        return {"message": "Item removed"}
    raise HTTPException(status_code=404, detail="Item not found")