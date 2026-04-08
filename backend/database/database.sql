-- =====================================================
-- 1. Таблица: пользователи (users)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    balance DECIMAL(10,2) DEFAULT 0.00,
    role TEXT DEFAULT 'user',
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
    price DECIMAL(10, 2) NOT NULL,
    category TEXT NOT NULL,
    calories NUMERIC NOT NULL,
    proteins NUMERIC NOT NULL,
    fats NUMERIC NOT NULL,
    carbs NUMERIC NOT NULL,
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

-- =====================================================
-- 7. Заполнение таблицы menu
-- =====================================================
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Рис с курицей и овощами', 320, 'gain', 600, 35, 15, 75, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Говядина с картофелем', 380, 'gain', 720, 42, 28, 65, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Протеиновый коктейл', 250, 'gain', 450, 45, 8, 50, '');

INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Греческий салат', 220, 'loss', 180, 8, 12, 10, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Запечённая рыба с овощами', 340, 'loss', 250, 28, 12, 15, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Овощной суп-пюре', 190, 'loss', 190, 5, 3, 18, '');

INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Паста с курицей и грибами', 350, 'maintain', 480, 32, 14, 58, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Тост с яйцом и авокадо', 270, 'maintain', 320, 14, 22, 24, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Гречка с куриной котлетой', 300, 'maintain', 450, 28, 16, 52, '');

INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Нут с тушеными овощами', 290, 'vegan', 380, 14, 8, 62, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Вегетерианский бургер', 310, 'vegan', 420, 16, 14, 58, '');
INSERT INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Киноа с запечёнными овощами', 340, 'vegan', 350, 12, 10, 54, '');
