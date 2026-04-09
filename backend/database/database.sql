-- =====================================================
-- 1. Таблица: пользователи (users)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
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
    address TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    description TEXT
);

-- =====================================================
-- 3. Таблица: меню (menu)
-- =====================================================
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
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
    status TEXT DEFAULT 'paid',   
    total_amount DECIMAL(10, 2) NOT NULL,
    pickup_code TEXT,
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
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Рис с курицей и овощами', 320, 'gain', 600, 35, 15, 75, '../img/menu/ris-ovoshhi-kuricza.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Говядина с картофелем', 380, 'gain', 720, 42, 28, 65, '../img/menu/beef-potato.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Протеиновый коктейль', 250, 'gain', 450, 45, 8, 50, '../img/menu/protein-cocktail.jpg');

INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Греческий салат', 220, 'loss', 180, 8, 12, 10, '../img/menu/greek-salad.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Запечённая рыба с овощами', 340, 'loss', 250, 28, 12, 15, '../img/menu/ryba-zapechennaja-s-ovoshhamii.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Овощной суп-пюре', 190, 'loss', 190, 5, 3, 18, '../img/menu/veg-soup.jpg');

INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Паста с курицей и грибами', 350, 'maintain', 480, 32, 14, 58, '../img/menu/Pasta-fetuchini-kuritsa-s-gribami-v-slivochnom-souse.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Тост с яйцом и авокадо', 270, 'maintain', 320, 14, 22, 24, '../img/menu/tost-s-avokado-i-yaicom.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Гречка с куриной котлетой', 300, 'maintain', 450, 28, 16, 52, '../img/menu/grechka-chicken.jpg');

INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Нут с тушеными овощами', 290, 'vegan', 380, 14, 8, 62, '../img/menu/nut-tushenyi-s-ovoshchami.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Вегетерианский бургер', 310, 'vegan', 420, 16, 14, 58, '../img/menu/vegan_burger.jpg');
INSERT OR IGNORE INTO menu(name, price, category, calories, proteins, fats, carbs, image_url) VALUES ('Киноа с запечёнными овощами', 340, 'vegan', 350, 12, 10, 54, '../img/menu/kinoa-baked-veges.jpg');

-- ========================================================
-- 8. Заполнение таблицы postomats
-- ========================================================

INSERT OR IGNORE INTO postomats (address, city, description) VALUES ("ул. Покрышкина, 4", "Москва", "Находится у главного входа");
INSERT OR IGNORE INTO postomats (address, city, description) VALUES ("пр-кт. Вернадского, 84с1", "Москва", "Рядом с библиотекой");
INSERT OR IGNORE INTO postomats (address, city, description) VALUES ("пр-кт. Вернадского, 78", "Москва", "1 этаж");