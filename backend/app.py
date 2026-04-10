import os
import sys
from fastapi import FastAPI, Depends, HTTPException, Header
from typing import List, Optional
import sqlite3
from contextlib import contextmanager
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from models.models import (
    UserCreate,
    UserResponse,
    MenuItemCreate,
    MenuItemResponse,
    CartItem,
    CartResponse,
    UpdateQuantityRequest,
    BalanceTopUp,
    BalanceResponse,
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    OrderStatusUpdate,
    PickupCode,
    PostomatCreate,
    PostomatUpdate,
    PostomatResponse,
    UserBlockRequest,
    UserLogin,
    LoginResponse
)
from database import database
from database.database import FoodDeliveryDB

app = FastAPI(title="Food Delivery API")

# Создаем глобальный экземпляр БД
db = FoodDeliveryDB("delivery.db")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
HTML_DIR = FRONTEND_DIR / "html"
STYLE_DIR = FRONTEND_DIR / "style"
IMG_DIR = FRONTEND_DIR / "img"

app.mount("/style", StaticFiles(directory=str(STYLE_DIR)), name="style")
app.mount("/img", StaticFiles(directory=str(IMG_DIR)), name="img")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HELPERS ====================

def require_admin(admin_id: int):
    """Проверка прав администратора. Кидает 403 если не админ."""
    admin = db.get_user(user_id=admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    if not db.is_admin(admin_id):
        raise HTTPException(status_code=403, detail="Access denied. Admin role required")
    return admin


def require_active_user(user_id: int):
    """Проверяет что пользователь существует и не заблокирован."""
    user = db.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user['is_active']:
        raise HTTPException(status_code=403, detail="User is blocked")
    return user

def require_self_or_admin(requester_id: int, target_user_id: int):
    """Проверяет, что запрашивающий — сам пользователь или админ."""
    requester = db.get_user(user_id=requester_id)
    if not requester:
        raise HTTPException(status_code=401, detail="Requester not found")
    if requester_id != target_user_id and not db.is_admin(requester_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return requester


# ==================== USERS ====================

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    """Создание пользователя"""
    user_id = db.add_user(user.email, user.password)
    if not user_id:
        raise HTTPException(status_code=400, detail="Email already exists")
    return db.get_user(user_id=user_id)

@app.post("/login", response_model=LoginResponse)
def login(data: UserLogin):
    """Авторизация пользователя"""
    user = db.authenticate_user(data.email, data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if not user['is_active']:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")

    return {
        "message": "Успешный вход",
        "user_id": user['id'],
        "email": user['email'],
        "role": user['role']
    }




@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, requester_id: int = Header(..., alias="X-User-Id")):
    """
    Получить пользователя по ID.
    - Обычный пользователь видит только себя
    - Админ видит любого
    """
    requester = db.get_user(user_id=requester_id)
    if not requester:
        raise HTTPException(status_code=401, detail="Requester not found")

    if requester_id != user_id and not db.is_admin(requester_id):
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own profile")

    user = db.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
# ==================== ADMIN: USERS ====================

@app.get("/admin/{admin_id}/users/", response_model=List[UserResponse])
def admin_get_all_users(admin_id: int, only_active: bool = False):
    """[ADMIN] Получить список всех пользователей"""
    require_admin(admin_id)
    return db.get_all_users(only_active=only_active)


@app.get("/admin/{admin_id}/users/{user_id}", response_model=UserResponse)
def admin_get_user(admin_id: int, user_id: int):
    """[ADMIN] Получить информацию о конкретном пользователе"""
    require_admin(admin_id)

    user = db.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch("/admin/{admin_id}/users/{user_id}/block")
def admin_block_user(admin_id: int, user_id: int, data: UserBlockRequest):
    """[ADMIN] Заблокировать / разблокировать пользователя"""
    require_admin(admin_id)

    if admin_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    if not db.set_user_active(user_id, data.is_active):
        raise HTTPException(status_code=404, detail="User not found")

    status = "unblocked" if data.is_active else "blocked"
    return {"message": f"User {user_id} {status}"}


@app.patch("/admin/{admin_id}/users/{user_id}/set-role")
def admin_set_role(admin_id: int, user_id: int, role: str):
    """[ADMIN] Назначить роль пользователю (user / admin)"""
    require_admin(admin_id)

    if role not in ('user', 'admin'):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")

    if not db.set_user_role(user_id, role):
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {user_id} role set to '{role}'"}

@app.patch("/admin/{admin_id}/orders/{order_id}/status")
def admin_update_order_status(admin_id: int, order_id: int, data: OrderStatusUpdate):
    """
    [ADMIN] Смена статуса заказа.
    Допустимые переходы:
      paid → in_transit → delivered → completed
    """
    require_admin(admin_id)

    result = db.update_order_status(order_id, data.status)

    if "error" in result:
        error_map = {
            "not_found": 404,
            "already_completed": 400,
            "invalid_transition": 400,
            "internal": 500,
        }
        status = error_map.get(result["error"], 400)
        raise HTTPException(status_code=status, detail=result["message"])

    return {
        "message": f"Статус заказа #{order_id} изменён",
        "old_status": result["old_status"],
        "new_status": result["new_status"]
    }


# ==================== BALANCE ====================

@app.post("/users/{user_id}/balance/topup", response_model=BalanceResponse)
def top_up_balance(
    user_id: int,
    data: BalanceTopUp,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ добавлено
):
    """Пополнить баланс пользователя"""
    require_self_or_admin(requester_id, user_id)                     # ✅ добавлено
    require_active_user(user_id)

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    new_balance = db.top_up_balance(user_id, data.amount)
    if new_balance is None:
        raise HTTPException(status_code=400, detail="Failed to top up balance")

    return {"user_id": user_id, "balance": new_balance}


@app.get("/users/{user_id}/balance", response_model=BalanceResponse)
def get_balance(
    user_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ добавлено
):
    """Получить баланс пользователя"""
    require_self_or_admin(requester_id, user_id)                     # ✅ добавлено

    balance = db.get_balance(user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "balance": balance}

# ==================== MENU ====================

@app.post("/menu/", response_model=MenuItemResponse)
def create_menu_item(
    item: MenuItemCreate,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ добавлено
):
    """[ADMIN] Добавить блюдо в меню"""
    require_admin(requester_id)                                      # ✅ добавлено

    item_id = db.add_menu_item(
        name=item.name,
        price=item.price,
        category=item.category,
        calories=item.calories,
        proteins=item.proteins,
        fats=item.fats,
        carbs=item.carbs,
        image_url=item.image_url
    )
    return db.get_menu_item(item_id)


@app.get("/menu/", response_model=List[MenuItemResponse])
def get_menu(category: Optional[str] = None):
    """Получить меню"""
    menu = db.get_menu(category=category)
    if menu is None:
        return []
    return menu


@app.get("/menu/{item_id}", response_model=MenuItemResponse)
def get_menu_item(item_id: int):
    """Получить блюдо по ID"""
    item = db.get_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.patch("/menu/{item_id}")
def update_menu_item(
    item_id: int,
    is_available: Optional[bool] = None,
    price: Optional[float] = None,
    requester_id: int = Header(..., alias="X-User-Id"),
):
    """[ADMIN] Обновить блюдо"""
    require_admin(requester_id)

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
def add_to_cart(
    user_id: int,
    item: CartItem,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ добавлено
):
    """Добавить товар в корзину"""
    require_self_or_admin(requester_id, user_id)                     # ✅ добавлено
    require_active_user(user_id)

    menu_item = db.get_menu_item(item.menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if db.add_to_cart(user_id, item.menu_item_id, item.quantity):
        return {"message": "Item added to cart"}
    raise HTTPException(status_code=400, detail="Failed to add to cart")


@app.get("/cart/{user_id}", response_model=List[CartResponse])
def get_cart(
    user_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ #8
):
    """Получить корзину"""
    require_self_or_admin(requester_id, user_id)                     # ✅ #8

    cart = db.get_cart(user_id)
    return cart                                                      # ✅ #4: было raise 404


@app.get("/cart/{user_id}/total")
def get_cart_total(
    user_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ добавлено
):
    """Получить сумму корзины"""
    require_self_or_admin(requester_id, user_id)                     # ✅ добавлено

    total = db.get_cart_total(user_id)
    return {"total": total}


@app.delete("/cart/{user_id}/clear")
def clear_cart(
    user_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ добавлено
):
    """Очистить корзину"""
    require_self_or_admin(requester_id, user_id)                     # ✅ добавлено

    db.clear_cart(user_id)
    return {"message": "Cart cleared"}


@app.delete("/cart/item/{cart_id}")
def remove_cart_item(
    cart_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),             # ✅ добавлено
):
    """Удалить товар из корзины"""
    cart_item = db.get_cart_item(cart_id)                             # ✅ проверка владельца
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found")

    require_self_or_admin(requester_id, cart_item["user_id"])        # ✅

    if db.remove_from_cart(cart_id):
        return {"message": "Item removed"}
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/cart/{user_id}/items/{cart_id}")
def update_cart_item_quantity(
    user_id: int,
    cart_id: int,
    request: UpdateQuantityRequest,
    requester_id: int = Header(..., alias="X-User-Id")
):
    """Обновление количества товара в корзине пользователя"""
    require_self_or_admin(requester_id, user_id)
    require_active_user(user_id)

    cart_item = db.get_cart_item(cart_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if cart_item["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if request.quantity == 0:
        if db.remove_from_cart(cart_id):
            return {"message": "Item removed from cart"}
        raise HTTPException(status_code=404, detail="Item not found")

    if db.update_cart_item(cart_id, request.quantity):
        return {"message": "Cart item quantity updated", "quantity": request.quantity}
    raise HTTPException(status_code=400, detail="Failed to update cart item")


# ==================== ORDERS (CHECKOUT) ====================

@app.post("/orders/{user_id}/checkout", response_model=OrderResponse)
def checkout(
    user_id: int,
    order_data: OrderCreate,
    requester_id: int = Header(..., alias="X-User-Id"),
):
    require_self_or_admin(requester_id, user_id)
    """
    Оплата заказа:
    - Проверяет баланс
    - Списывает деньги
    - Переносит корзину в историю заказов
    - Очищает корзину
    """
    require_active_user(user_id)

    result = db.create_order_from_cart(
        user_id=user_id,
        postomat_id=order_data.postomat_id,
        comment=order_data.comment
    )

    # Обработка ошибок из БД
    if "error" in result:
        error_map = {
            "postomat_required":400,
            "cart_empty": 400,
            "user_not_found": 404,
            "insufficient_funds": 402,
            "postomat_not_found": 404,
            "internal": 500,
        }
        status = error_map.get(result["error"], 400)
        raise HTTPException(status_code=status, detail=result["message"])

    # Возвращаем полный заказ
    order = db.get_order(result["order_id"])
    return order


@app.get("/orders/{user_id}", response_model=List[OrderResponse])
def get_user_orders(
    user_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),             
):
    """Получить историю заказов пользователя"""
    require_self_or_admin(requester_id, user_id)

    user = db.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders = db.get_user_orders(user_id)
    return orders

@app.get("/orders/detail/{order_id}", response_model=OrderResponse)
def get_order_detail(
    order_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),
):
    """Получить детали конкретного заказа"""
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    require_self_or_admin(requester_id, order["user_id"])
    return order

@app.post("/postomats/{postomat_id}/pickup")
def pickup_order(postomat_id: int, data: PickupCode):
    """
    Ввод кода получения на постомате.
    Меняет статус с 'delivered' на 'completed'.
    """
    postomat = db.get_postomat(postomat_id)
    if not postomat:
        raise HTTPException(status_code=404, detail="Постомат не найден")

    if not postomat['is_active']:
        raise HTTPException(status_code=400, detail="Постомат неактивен")

    result = db.complete_order_by_code(postomat_id, data.code)

    if "error" in result:
        error_map = {
            "not_found": 404,
            "already_completed": 400,
            "not_ready": 409,
            "internal": 500,
        }
        status = error_map.get(result["error"], 400)
        raise HTTPException(status_code=status, detail=result["message"])

    return result

@app.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    requester_id: int = Header(..., alias="X-User-Id"),
):
    """Отмена заказа пользователем (с возвратом средств)"""
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    require_self_or_admin(requester_id, order["user_id"])
    require_active_user(order["user_id"])

    result = db.cancel_order(order_id)

    if "error" in result:
        error_map = {
            "not_found": 404,
            "already_cancelled": 400,
            "already_completed": 400,
            "internal": 500,
        }
        status = error_map.get(result["error"], 400)
        raise HTTPException(status_code=status, detail=result["message"])

    return {
        "message": f"Заказ #{order_id} отменён",
        "refund": result["refund"]
    }

@app.post("/admin/{admin_id}/orders/{order_id}/cancel")
def admin_cancel_order(admin_id: int, order_id: int):
    """[ADMIN] Отмена заказа (с возвратом средств пользователю)"""
    require_admin(admin_id)

    result = db.cancel_order(order_id)

    if "error" in result:
        error_map = {
            "not_found": 404,
            "already_cancelled": 400,
            "already_completed": 400,
            "internal": 500,
        }
        status = error_map.get(result["error"], 400)
        raise HTTPException(status_code=status, detail=result["message"])

    return {
        "message": f"Заказ #{order_id} отменён администратором",
        "refund": result["refund"],
        "user_id": result["user_id"]
    }



# ==================== POSTOMATS ====================

@app.get("/postomats/", response_model=List[PostomatResponse])
def get_postomats():
    """Получить список активных постоматов"""
    return db.get_all_postomats(only_active=True)


@app.get("/postomats/{postomat_id}", response_model=PostomatResponse)
def get_postomat(postomat_id: int):
    """Получить постомат по ID"""
    postomat = db.get_postomat(postomat_id)
    if not postomat:
        raise HTTPException(status_code=404, detail="Postomat not found")
    return postomat


# ==================== ADMIN: POSTOMAT ====================

@app.post("/admin/{admin_id}/postomats/", response_model=PostomatResponse)
def admin_create_postomat(admin_id: int, data: PostomatCreate):
    """[ADMIN] Создать постомат"""
    require_admin(admin_id)

    postomat_id = db.add_postomat(
        address=data.address,
        city=data.city,
        description=data.description
    )
    if not postomat_id:
        raise HTTPException(status_code=400, detail="Failed to create postomat")

    return db.get_postomat(postomat_id)


@app.patch("/admin/{admin_id}/postomats/{postomat_id}", response_model=PostomatResponse)
def admin_update_postomat(admin_id: int, postomat_id: int, data: PostomatUpdate):
    """[ADMIN] Редактирование информации о постомате"""
    require_admin(admin_id)

    updates = {}
    if data.address is not None:
        updates['address'] = data.address
    if data.city is not None:
        updates['city'] = data.city
    if data.is_active is not None:
        updates['is_active'] = data.is_active
    if data.description is not None:
        updates['description'] = data.description

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if not db.update_postomat(postomat_id, **updates):
        raise HTTPException(status_code=404, detail="Postomat not found")

    return db.get_postomat(postomat_id)
@app.delete("/admin/{admin_id}/postomats/{postomat_id}")
def admin_delete_postomat(admin_id: int, postomat_id: int):
    """[ADMIN] Удалить постомат (только если нет привязанных заказов)"""
    require_admin(admin_id)

    if not db.delete_postomat(postomat_id):
        raise HTTPException(status_code=400, detail="Cannot delete postomat (not found or has linked orders)")

    return {"message": f"Postomat {postomat_id} deleted"}

# ========================FRONTEND================================

@app.get("/")
async def root():
    return FileResponse(str(HTML_DIR / "main.html"))

@app.get("/menu")
async def root():
    return FileResponse(str(HTML_DIR / "menu.html"))

@app.get("/account")
async def root():
    return FileResponse(str(HTML_DIR / "account.html"))

@app.get("/cart")
async def root():
    return FileResponse(str(HTML_DIR / "cart.html"))

@app.get("/orders")
async def root():
    return FileResponse(str(HTML_DIR / "curr_and_history_orders.html"))