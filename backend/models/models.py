from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен быть не менее 6 символов')
        return v

class UserLogin(BaseModel):
    """Схема для входа"""
    email: EmailStr
    password: str
    
class LoginResponse(BaseModel):
    """Ответ при успешном логине"""
    message: str
    user_id: int
    email: str
    role: str
    
class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: int
    email: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: int
    email: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True



# ==================== BALANCE SCHEMAS ===================
class BalanceTopUp (BaseModel):
    """Схема для пополнения счета пользователя"""
    amount: float
class BalanceResponse(BaseModel):
    """Вывод текущего баланса пользователя"""
    user_id: int
    balance: float
# ==================== MENU SCHEMAS ====================

class MenuItemCreate(BaseModel):
    """Схема для создания блюда"""
    name: str
    price: float
    category: str
    calories: int
    proteins: int
    fats: int
    carbs: int
    image_url: Optional[str] = None


class MenuItemResponse(BaseModel):
    """Схема для ответа с данными блюда"""
    id: int
    name: str
    price: float
    category: str
    calories: int
    proteins: int
    fats: int
    carbs: int
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
    category: Optional[str] = None
    image_url: Optional[str] = None
    calories: Optional[int] = None
    proteins: Optional[int] = None
    fats: Optional[int] = None
    carbs: Optional[int] = None
    quantity: int
    price: float
    subtotal: float
    added_at: datetime

    class Config:
        from_attributes = True
# ==================== ORDER SCHEMAS =====================

class OrderCreate(BaseModel):
    """Схема для оформления заказа после оплаты корзины"""
    postomat_id: int
    comment: Optional[str] = None
    
class OrderStatusUpdate(BaseModel):
    """Схема для смены статуса заказа администратором"""
    status: str
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed = ('paid', 'in_transit', 'delivered', 'completed')
        if v not in allowed:
            raise ValueError(f'Статус должен быть одним из: {", ".join(allowed)}')
        return v

class PickupCode(BaseModel):
    """Схема для ввода кода полусения"""
    code: str

class OrderItemResponse(BaseModel):
    """Схема для состава заказа"""
    id: int
    menu_item_id: int
    name: str
    quantity: int
    price_at_time: float
    subtotal: float
    
    class Config:
        from_attributes = True
        
class OrderResponse(BaseModel):
    """Схема для ответа с данными заказа"""
    id: int
    user_id: int
    postomat_id: int
    postomat_address: str
    postomat_city: str
    order_date: datetime
    status: str
    total_amount: float
    pickup_code: Optional[str] = None
    comment: Optional[str]= None
    items: List[OrderItemResponse]= []
    
    class Config:
        from_attributes = True
        
    

# ================= POSTOMAT SCHEMAS ==================

class PostomatCreate(BaseModel):
    """Схема для создания постомата"""
    address: str
    city: str
    description: Optional[str]= None
    
class PostomatUpdate(BaseModel):
    """Схема для обновления данных о постамате"""
    address: Optional[str]= None
    city:Optional[str]= None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class PostomatResponse(BaseModel):
    """Схема для ответа с данными постомата"""
    id: int
    address:str
    city: str
    is_active: bool
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

# ================== ADMIN SCHEMAS =====================

class UserBlockRequest(BaseModel):
    """Схема для блокировки/разблокировки пользователей"""

    is_active: bool

class UserLogin(BaseModel):
    """Схема для входа"""
    email: EmailStr
    password: str
    
class LoginResponse(BaseModel):
    """Ответ при успешном логине"""
    message: str
    user_id: int
    email: str
    role: str
    is_active: bool
