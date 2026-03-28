-- =====================================================
-- 1. Таблица: пользователи (users)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- =====================================================
-- 2. Таблица: постоматы (lockers / postomats)
-- =====================================================
CREATE TABLE IF NOT EXISTS postomats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    description TEXT
);

-- =====================================================
-- 3. Таблица: меню (menu)
-- =====================================================
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category TEXT,
    is_available BOOLEAN DEFAULT 1,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. Таблица: корзина (cart)
-- =====================================================
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu(id) ON DELETE CASCADE
);

-- =====================================================
-- 5. Таблица: заказы (orders) - История заказов
-- =====================================================
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    postomat_id INTEGER,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new',              -- Статус: new, cooking, ready, delivered, cancelled
    total_amount DECIMAL(10, 2) NOT NULL,
    delivery_address TEXT,
    comment TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (postomat_id) REFERENCES postomats(id) ON DELETE SET NULL
);

-- =====================================================
-- 6. Таблица: состав заказа (order_items)
-- =====================================================
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_time DECIMAL(10, 2) NOT NULL,

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu(id) ON DELETE RESTRICT
);
