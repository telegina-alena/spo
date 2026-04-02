import sqlite3
import os


class FoodDeliveryDB:
    def __init__(self, db_name='delivery.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Инициализация БД"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(current_dir, 'database.sql')
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            schema = f.read()

        conn = sqlite3.connect(self.db_name)
        conn.executescript(schema)
        conn.close()
        print("База данных инициализирована")

    # ==================== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ====================

    def add_user(self, email):
        """Добавление пользователя (только email)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (email)
                VALUES (?)
            """, (email,))
            conn.commit()
            user_id = cursor.lastrowid
            print(f"Пользователь с email {email} добавлен с ID {user_id}")
            return user_id
        except sqlite3.IntegrityError as e:
            print(f"Ошибка: пользователь с таким email уже существует")
            return None
        finally:
            conn.close()

    def get_user(self, user_id=None, email=None):
        """Получение информации о пользователе"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        elif email:
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

    # ==================== РАБОТА С МЕНЮ ====================

    def add_menu_item(self, name, price, category=None, description=None, image_url=None):
        """Добавление блюда в меню"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO menu (name, description, price, category, image_url)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, price, category, image_url))
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
                'description': row['description'],
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
            print(f"Блюдо {item_id} обновлено")
            return True
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
            print(f"Товар удален из корзины")
            return True
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

# ==================== ПРИМЕР ИСПОЛЬЗОВАНИЯ ====================

def main():
    db = FoodDeliveryDB()

if __name__ == "__main__":
    main()