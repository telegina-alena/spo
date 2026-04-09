import sqlite3
import os
import bcrypt
import secrets

class FoodDeliveryDB:
    def __init__(self, db_name='delivery.db'):
        self.db_name = db_name
        self.init_database()
        self.ensure_admin_exists()  # ← добавить



    def init_database(self):
        """Инициализация БД"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(current_dir, 'database.sql')
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            schema = f.read()


        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.executescript(schema)
        conn.close()
        print("База данных инициализирована")

    # ==================== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ====================

    def add_user(self, email, password):
        """Добавление пользователя с хешированным паролем"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Хешируем пароль
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        try:
            cursor.execute("""
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
            """, (email, password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            print(f"Пользователь с email {email} добавлен с ID {user_id}")
            return user_id
        except sqlite3.IntegrityError:
            print(f"Ошибка: пользователь с таким email уже существует")
            return None
        finally:
            conn.close()
            
    def authenticate_user(self, email, password):
        """Проверка логина и пароля. Возвращает пользователя или None"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            return None

        # Проверяем пароль через bcrypt
        password_bytes = password.encode('utf-8')
        hash_bytes = user['password_hash'].encode('utf-8')

        if bcrypt.checkpw(password_bytes, hash_bytes):
            return dict(user)
        return None



    def get_user(self, user_id=None, email=None):
        """Получение информации о пользователе"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if user_id is not None:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        elif email is not None:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        else:
            conn.close()
            return None

        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def update_user(self, user_id, email=None, is_active=None):
        """Обновление данных пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        updates = []
        values = []

        if email is not None:
            updates.append("email = ?")
            values.append(email)

        if is_active is not None:
            updates.append("is_active = ?")
            values.append(is_active)

        if not updates:
            conn.close()
            return False

        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

        try:
            cursor.execute(query, values)
            conn.commit()
            print(f"Данные пользователя {user_id} обновлены")
            return True
        except Exception as e:
            print(f"Ошибка обновления: {e}")
            return False
        finally:
            conn.close()

    def get_all_users(self, only_active=True):
        """Получение всех пользователей"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if only_active:
            cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")

        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    # ==================== ДЕНЕЖНЫЙ БАЛАНС =====================
    
    def top_up_balance(self, user_id, amount):
        """Пополнение баланса пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE id = ?",
                (amount, user_id)
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            new_balance = cursor.fetchone()[0]
            print(f"Баланс пользователя {user_id} пополнен на {amount}. Новый баланс: {new_balance}")
            return float(new_balance)
        except Exception as e:
            print(f"Ошибка пополнения баланса: {e}")
            return None
        finally:
            conn.close()
            
    def get_balance(self, user_id):
        """Получение информации о балансе пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        return float(row[0])
        
    def deduct_balance(self, user_id, amount):
        """Списание средств с баланса"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            #Проверка на количество средств
            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row is None:
                return False
            
            current_balance = float(row[0])
            if current_balance < amount:
                return False
            
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE id = ?",
                (amount, user_id)
            )
            conn.commit()
            print(f"С баланса пользователя {user_id} списано {amount}")
            return True
        except Exception as e:
            print(f"Ошибка списания: {e}")
            return False
        finally:
            conn.close()
    # ==================== РАБОТА С МЕНЮ ====================

    def add_menu_item(self, name, price, calories, proteins, fats, carbs, image_url=None, category=None,):
        """Добавление блюда в меню"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO menu (name, calories, proteins, fats, carbs, price, category, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, calories, proteins, fats, carbs, price, category, image_url))
        conn.commit()
        menu_id = cursor.lastrowid
        conn.close()

        print(f"Блюдо {name} добавлено в меню с ID {menu_id}")
        return menu_id

    def get_menu(self, category=None, only_available=True):
        """Получение меню"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM menu WHERE 1=1"
        params = []

        if only_available:
            query += " AND is_available = 1"

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY category, name"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Преобразуем в список словарей
        menu_items = []
        for row in rows:
            menu_items.append({
                'id': row['id'],
                'name': row['name'],
                'price': float(row['price']),  # убедимся что float
                'category': row['category'],
                'calories': row['calories'],
                'proteins': row['proteins'],
                'fats': row['fats'],
                'carbs': row['carbs'],
                'is_available': bool(row['is_available']),
                'image_url': row['image_url'],
                'created_at': row['created_at']
            })

        conn.close()
        return menu_items  # всегда возвращаем список
    def get_menu_item(self, item_id):
        """Получение информации о блюде"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM menu WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        conn.close()

        return dict(item) if item else None

    def update_menu_item(self, item_id, **kwargs):
        """Обновление блюда в меню"""
        if not kwargs:
            return False

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [item_id]

        try:
            cursor.execute(f"UPDATE menu SET {set_clause} WHERE id = ?", values)
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                print(f"Блюдо {item_id} обновлено")
            return success
        except Exception as e:
            print(f"Ошибка обновления: {e}")
            return False
        finally:
            conn.close()

    # ==================== РАБОТА С КОРЗИНОЙ ====================

    def add_to_cart(self, user_id, menu_item_id, quantity=1):
        """Добавление товара в корзину"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            # Проверяем, есть ли уже такой товар в корзине
            cursor.execute("""
                SELECT id, quantity FROM cart 
                WHERE user_id = ? AND menu_item_id = ?
            """, (user_id, menu_item_id))

            existing = cursor.fetchone()

            if existing:
                # Обновляем количество
                new_quantity = existing[1] + quantity
                cursor.execute("""
                    UPDATE cart SET quantity = ? 
                    WHERE user_id = ? AND menu_item_id = ?
                """, (new_quantity, user_id, menu_item_id))
                print(f"Обновлено количество товара в корзине: {new_quantity}")
            else:
                # Добавляем новый товар
                cursor.execute("""
                    INSERT INTO cart (user_id, menu_item_id, quantity)
                    VALUES (?, ?, ?)
                """, (user_id, menu_item_id, quantity))
                print(f"Товар добавлен в корзину")

            conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления в корзину: {e}")
            return False
        finally:
            conn.close()

    def get_cart(self, user_id):
        """Получение содержимого корзины"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                c.id,
                c.quantity,
                c.added_at,
                m.id as menu_item_id,
                m.name,
                m.price,
                m.category,
                (c.quantity * m.price) as subtotal
            FROM cart c
            JOIN menu m ON c.menu_item_id = m.id
            WHERE c.user_id = ?
            ORDER BY c.added_at
        """, (user_id,))

        cart_items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cart_items

    def get_cart_total(self, user_id):
        """Получение общей суммы корзины"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT SUM(c.quantity * m.price) as total
            FROM cart c
            JOIN menu m ON c.menu_item_id = m.id
            WHERE c.user_id = ?
        """, (user_id,))

        total = cursor.fetchone()[0]
        conn.close()
        return total or 0.0

    def update_cart_item(self, cart_id, quantity):
        """Обновление количества товара в корзине"""
        if quantity <= 0:
            return self.remove_from_cart(cart_id)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_id))
            conn.commit()
            print(f"Количество товара обновлено на {quantity}")
            return True
        except Exception as e:
            print(f"Ошибка обновления: {e}")
            return False
        finally:
            conn.close()

    def remove_from_cart(self, cart_id):
        """Удаление товара из корзины"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                print(f"Товар удален из корзины")
            return success
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False
        finally:
            conn.close()

    def clear_cart(self, user_id):
        """Очистка всей корзины пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            conn.commit()
            print(f"Корзина очищена")
            return True
        except Exception as e:
            print(f"Ошибка очистки корзины: {e}")
            return False
        finally:
            conn.close()
    def get_cart_item(self, cart_id):
        """Получение записи корзины по ID (для проверки владельца)"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cart WHERE id = ?", (cart_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

# ==================== ЗАКАЗЫ =======================

    def create_order_from_cart(self, user_id, postomat_id, comment=None):
        """Оформление заказа"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if not postomat_id:
                return {"error": "postomat_required", "message": "Необходимо выбрать постомат для доставки"}

            cursor.execute("SELECT id, address, city FROM postomats WHERE id = ? AND is_active = 1", (postomat_id,))
            postomat = cursor.fetchone()
            if postomat is None:
                return {"error": "postomat_not_found", "message": "Постомат не найден или неактивен"}

            cursor.execute("""
                SELECT c.menu_item_id, c.quantity, m.price
                FROM cart c
                JOIN menu m ON c.menu_item_id = m.id
                WHERE c.user_id = ?
            """, (user_id,))
            cart_items = cursor.fetchall()

            if not cart_items:
                return {"error": "cart_empty", "message": "Корзина пуста"}

            total = sum(row['quantity'] * float(row['price']) for row in cart_items)

            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row is None:
                return {"error": "user_not_found", "message": "Пользователь не найден"}

            balance = float(user_row['balance'])
            if balance < total:
                return {
                    "error": "insufficient_funds",
                    "message": f"Недостаточно средств. Баланс: {balance}, сумма заказа: {total}"
                }

            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE id = ?",
                (total, user_id)
            )

            # ── Генерация кода получения ──
            pickup_code = self._generate_pickup_code()

            cursor.execute("""
                INSERT INTO orders (user_id, postomat_id, total_amount, pickup_code, status, comment)
                VALUES (?, ?, ?, ?, 'paid', ?)
            """, (user_id, postomat_id, total, pickup_code, comment))

            order_id = cursor.lastrowid

            for item in cart_items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_time)
                    VALUES (?, ?, ?, ?)
                """, (order_id, item['menu_item_id'], item['quantity'], float(item['price'])))

            cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

            conn.commit()
            print(f"Заказ #{order_id} создан. Код получения: {pickup_code}. Сумма: {total}")
            return {"order_id": order_id, "total": total, "pickup_code": pickup_code}

        except Exception as e:
            conn.rollback()
            print(f"Ошибка создания заказа: {e}")
            return {"error": "internal", "message": str(e)}
        finally:
            conn.close()

    def get_order(self, order_id):
        """Информация о заказе, включая состав заказа и постамат"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Адресс
        cursor.execute("""
            SELECT 
                o.*,
                p.address as postomat_address,
                p.city as postomat_city
            FROM orders o
            LEFT JOIN postomats p ON o.postomat_id = p.id
            WHERE o.id = ?
        """, (order_id,))
        order_row = cursor.fetchone()
        if not order_row:
            conn.close()
            return None
        order = dict(order_row)
        
        #Состав заказа
        cursor.execute("""
            SELECT 
                oi.id,
                oi.menu_item_id,
                oi.quantity,
                oi.price_at_time,
                m.name,
                (oi.quantity * oi.price_at_time) as subtotal
            FROM order_items oi
            JOIN menu m ON oi.menu_item_id = m.id
            WHERE oi.order_id = ?
        """, (order_id,))
        order['items'] = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return order
    def get_user_orders(self, user_id):
        """Получение истории заказов пользователя"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                o.*,
                p.address as postomat_address,
                p.city as postomat_city
            FROM orders o
            LEFT JOIN postomats p ON o.postomat_id = p.id
            WHERE o.user_id = ?
            ORDER BY o.order_date DESC
        """, (user_id,))

        orders = []
        for order_row in cursor.fetchall():
            order = dict(order_row)

            # Получаем состав для каждого заказа
            cursor.execute("""
                SELECT 
                    oi.id,
                    oi.menu_item_id,
                    oi.quantity,
                    oi.price_at_time,
                    m.name,
                    (oi.quantity * oi.price_at_time) as subtotal
                FROM order_items oi
                JOIN menu m ON oi.menu_item_id = m.id
                WHERE oi.order_id = ?
            """, (order['id'],))

            order['items'] = [dict(row) for row in cursor.fetchall()]
            orders.append(order)

        conn.close()
        return orders
    
    def _generate_pickup_code(self):
        """Генерация кода получения"""
        return f"{secrets.randbelow(1000000):06d}"
    
    def complete_order_by_code(self, postomat_id, code):
        """Завершение заказа по коду получения на постомате"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, status, user_id
                FROM orders
                WHERE postomat_id = ? AND pickup_code = ?
            """, (postomat_id, code))

            order = cursor.fetchone()

            if order is None:
                return {"error": "not_found", "message": "Заказ с таким кодом не найден на этом постомате"}

            if order['status'] == 'completed':
                return {"error": "already_completed", "message": "Заказ уже получен"}

            if order['status'] != 'delivered':
                status_messages = {
                    'paid': 'Заказ ещё не отправлен',
                    'in_transit': 'Заказ ещё в пути',
                }
                msg = status_messages.get(order['status'], f"Текущий статус: {order['status']}")
                return {"error": "not_ready", "message": msg}

            cursor.execute(
                "UPDATE orders SET status = 'completed' WHERE id = ?",
                (order['id'],)
            )
            conn.commit()
            print(f"Заказ #{order['id']} завершён по коду {code}")
            return {
                "success": True,
                "order_id": order['id'],
                "message": "Заказ успешно получен!"
            }

        except Exception as e:
            print(f"Ошибка завершения заказа: {e}")
            return {"error": "internal", "message": str(e)}
        finally:
            conn.close()


    # ==================== ПОСТОМАТЫ ====================

    def add_postomat(self, address, city, description=None):
        """Добавление постомата"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO postomats (address, city, description)
                VALUES (?, ?, ?)
            """, (address, city, description))
            conn.commit()
            postomat_id = cursor.lastrowid
            print(f"Постомат добавлен с ID {postomat_id}")
            return postomat_id
        except Exception as e:
            print(f"Ошибка добавления постомата: {e}")
            return None
        finally:
            conn.close()

    def get_postomat(self, postomat_id):
        """Получение информации о постомате"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM postomats WHERE id = ?", (postomat_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_postomats(self, only_active=True):
        """Получение всех постоматов"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if only_active:
            cursor.execute("SELECT * FROM postomats WHERE is_active = 1 ORDER BY city, address")
        else:
            cursor.execute("SELECT * FROM postomats ORDER BY city, address")

        postomats = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return postomats

    def update_postomat(self, postomat_id, **kwargs):
        """Обновление постомата"""
        if not kwargs:
            return False

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [postomat_id]

        try:
            cursor.execute(f"UPDATE postomats SET {set_clause} WHERE id = ?", values)
            conn.commit()

            if cursor.rowcount == 0:
                return False

            print(f"Постомат {postomat_id} обновлён")
            return True
        except Exception as e:
            print(f"Ошибка обновления постомата: {e}")
            return False
        finally:
            conn.close()
    def delete_postomat(self, postomat_id):
        """Удаление постомата (только если нет привязанных заказов)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            # Проверяем наличие заказов на этот постомат
            cursor.execute("SELECT COUNT(*) FROM orders WHERE postomat_id = ?", (postomat_id,))
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"Нельзя удалить постомат {postomat_id}: есть {count} привязанных заказов")
                return False

            cursor.execute("DELETE FROM postomats WHERE id = ?", (postomat_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return False

            print(f"Постомат {postomat_id} удалён")
            return True
        except Exception as e:
            print(f"Ошибка удаления постомата: {e}")
            return False
        finally:
            conn.close()

    # ==================== АДМИН ====================

    def set_user_active(self, user_id, is_active):
        """Блокировка / разблокировка пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET is_active = ? WHERE id = ?",
                (1 if is_active else 0, user_id)
            )
            conn.commit()

            if cursor.rowcount == 0:
                return False

            status = "разблокирован" if is_active else "заблокирован"
            print(f"Пользователь {user_id} {status}")
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
        finally:
            conn.close()

    def is_admin(self, user_id):
        """Проверка, является ли пользователь админом"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return False
        return row[0] == 'admin'

    def set_user_role(self, user_id, role):
        """Установка роли пользователя (для первоначальной настройки)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
        finally:
            conn.close()
            
    def update_order_status(self, order_id, new_status):
        """Обновление статуса заказа с проверкой допустимых переходов"""
        # Допустимые переходы статусов
        allowed_transitions = {
            'paid': 'in_transit',
            'in_transit': 'delivered',
            'delivered': 'completed',
        }

        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()

            if row is None:
                return {"error": "not_found", "message": "Заказ не найден"}

            current_status = row['status']

            if current_status == 'completed':
                return {"error": "already_completed", "message": "Заказ уже завершён"}

            expected_next = allowed_transitions.get(current_status)
            if new_status != expected_next:
                return {
                    "error": "invalid_transition",
                    "message": f"Нельзя сменить статус с '{current_status}' на '{new_status}'. "
                            f"Допустимый следующий статус: '{expected_next}'"
                }

            cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (new_status, order_id)
            )
            conn.commit()
            print(f"Заказ #{order_id}: {current_status} → {new_status}")
            return {"success": True, "old_status": current_status, "new_status": new_status}

        except Exception as e:
            print(f"Ошибка смены статуса: {e}")
            return {"error": "internal", "message": str(e)}
        finally:
            conn.close()


    def ensure_admin_exists(self, email="admin@delivery.local", password="admin123"):
        """Создаёт админа, если в системе нет ни одного"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        count = cursor.fetchone()[0]

        if count == 0:
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            cursor.execute(
                "INSERT OR IGNORE INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
                (email, password_hash)
            )
            conn.commit()
            print(f"Создан начальный админ: {email} / {password}")

        conn.close()


def main():
    db = FoodDeliveryDB()

if __name__ == "__main__":
    main()