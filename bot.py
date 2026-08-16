import nest_asyncio
nest_asyncio.apply()
import sqlite3
import html
import logging
import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

try:
    import httpx
except ImportError:
    raise ImportError("مكتبة httpx غير مثبتة. شغل: pip install httpx")

BOT_TOKEN = "8141024354:AAFGwx-UzRfQhZlOypUmRG_kTtPMIzDqllA"
ADMIN_IDS = [5811814277]
ADMIN_SECRET = "TammSecret9"
DB_PATH = "bot_database.db"

FAWATERK_CLIENT_ID = "a279f5d4-f0e8-4c32-8c04-a58225c4b69b"
FAWATERK_CLIENT_SECRET = "42VfUs6824SJM7tqRvTTuow39S5AYxIkHfOS1lPM"
FAWATERK_API_BASE = "https://app.fawaterk.com"

WALLET_NUMBER = "01018484572"
WALLET_NAME = "محمود"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def generate_auto_description(product_name):
    """توليد وصف تلقائي بسيط"""
    name = product_name.lower()
    if any(x in name for x in ["capcut", "كاب كات", "كابكات"]):
        return "🎬 تعديل فيديو احترافي بدون علامة مائية مع كل الفلاتر والمؤثرات والأدوات المتاحة للمحترفين."
    elif any(x in name for x in ["netflix", "نتفليكس"]):
        return "🎬 مشاهدة الأفلام والمسلسلات بجودة UHD 4K على 4 شاشات في نفس الوقت بدون أي إعلانات."
    elif any(x in name for x in ["spotify", "سبوتيفاي"]):
        return "🎵 استماع بدون إعلانات بجودة عالية جداً مع إمكانية التحميل للاستماع بدون إنترنت."
    elif any(x in name for x in ["chatgpt", "chat gpt", "شات جي بي تي", "gpt"]):
        return "🤖 الوصول الكامل لـ GPT-4 و GPT-4o مع إنشاء صور DALL-E وتصفح سريع بدون تقطيع."
    elif any(x in name for x in ["canva", "كانفا"]):
        return "🎨 كل القوالب الاحترافية مع أدوات Brand Kit وBackground Remover وتصميم فوري."
    elif any(x in name for x in ["youtube", "يوتيوب", "يوتيوب بريميوم"]):
        return "📺 مشاهدة بدون إعلانات مع خلفية مشغلة وتحميل الفيديوهات للمشاهدة بدون إنترنت."
    elif any(x in name for x in ["crunchyroll", "كرنشي", "انمي"]):
        return "🎌 مشاهدة الأنمي بجودة عالية مع ترجمة فورية وحلقات جديدة فوراً."
    elif any(x in name for x in ["apple", "آبل", "ايفون"]):
        return "🍎 خدمة أبل المميزة مع كل المزايا الحصرية والتحديثات المستمرة."
    elif any(x in name for x in ["steam", "ستيم", "لعبة"]):
        return "🎮 عالم الألعاب الرقمية مع كل الإضافات والمحتويات الحصرية."
    elif any(x in name for x in ["adobe", "أدوبي", "فوتوشوب"]):
        return "🎨 أدوات التصميم الاحترافية من أدوبي مع كل التحديثات والميزات الجديدة."
    elif any(x in name for x in ["vpn", "في بي ان"]):
        return "🔒 تصفح آمن وخاص مع سرعات عالية وخوادم في كل أنحاء العالم."
    else:
        return f"✨ خدمة {product_name} مميزة بأعلى جودة وأفضل سعر في السوق مع ضمان كامل وتسليم فوري."


# ==================== ENHANCED DATABASE ====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            balance REAL DEFAULT 0,
            join_date TEXT,
            order_count INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            language TEXT DEFAULT 'ar',
            notes TEXT DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            stock INTEGER,
            warranty INTEGER,
            emoji TEXT,
            discount INTEGER DEFAULT 0,
            features TEXT,
            category TEXT,
            display_order INTEGER DEFAULT 0,
            requires_account INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            sales_count INTEGER DEFAULT 0,
            image_file_id TEXT DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_price REAL,
            status TEXT DEFAULT 'pending',
            order_date TEXT,
            payment_method TEXT,
            client_email TEXT,
            delivered_email TEXT,
            delivered_password TEXT,
            fawaterk_invoice_id TEXT DEFAULT '',
            admin_notes TEXT DEFAULT '',
            coupon_code TEXT DEFAULT '',
            discount_amount REAL DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recharges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            phone_number TEXT,
            status TEXT DEFAULT 'pending',
            request_date TEXT,
            fawaterk_invoice_id TEXT DEFAULT '',
            admin_notes TEXT DEFAULT '',
            proof_image TEXT DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_sessions (
            user_id INTEGER PRIMARY KEY,
            is_active INTEGER DEFAULT 0,
            granted_at TEXT,
            role TEXT DEFAULT 'admin'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            discount_percent INTEGER,
            max_uses INTEGER,
            used_count INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TEXT,
            expires_at TEXT,
            is_active INTEGER DEFAULT 1,
            min_order_amount REAL DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            target_type TEXT,
            target_id TEXT,
            details TEXT,
            created_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            emoji TEXT DEFAULT '📁',
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    ''')

    defaults = [
        ('wallet_number', WALLET_NUMBER),
        ('wallet_name', WALLET_NAME),
        ('usdt_address', '1267938246'),
        ('support_username', '@m_f0den'),
        ('bot_name', 'Tamm Shop'),
        ('welcome_message', 'أهلاً بيك في المتجر!'),
        ('maintenance_mode', '0'),
        ('min_recharge', '5'),
        ('min_order', '5'),
        ('usd_rate', '50'),
    ]
    for k, v in defaults:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                       (k, v, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cats = [('تطبيقات', '📱', 1), ('ذكاء اصطناعي', '🤖', 2), ('بث', '🎬', 3), ('موسيقى', '🎵', 4), ('تصميم', '🎨', 5)]
        cursor.executemany("INSERT INTO categories (name, emoji, display_order) VALUES (?, ?, ?)", cats)

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ("CapCut Pro 1M (28DW)", 115.0, 8, 30, "🛍", 27, "تعديل فيديو احترافي|بدون علامة مائية|كل الفلاتر", "تطبيقات", 1, 0, ""),
            ("ChatGPT Plus 1M", 250.0, 15, 30, "🤖", 15, "GPT-4 و GPT-4o|صور DALL-E|تصفح سريع", "ذكاء اصطناعي", 2, 1, ""),
            ("Netflix Premium 1M", 80.0, 20, 7, "🎬", 20, "UHD 4K|4 شاشات|بدون إعلانات", "بث", 3, 1, ""),
            ("Spotify Premium 1M", 45.0, 25, 15, "🎵", 10, "بدون إعلانات|جودة عالية|تحميل offline", "موسيقى", 4, 1, ""),
            ("Canva Pro 1Y", 350.0, 5, 365, "🎨", 30, "كل القوالب|Brand Kit|Background Remover", "تصميم", 5, 0, ""),
        ]
        cursor.executemany('''
            INSERT INTO products (name, price, stock, warranty, emoji, discount, features, category, display_order, requires_account, created_at, image_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), p[10]) for p in sample_products])

    conn.commit()
    conn.close()
    print("✅ قاعدة البيانات المحسنة جاهزة 100%!")


def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    if "image_file_id" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN image_file_id TEXT DEFAULT ''")
        conn.commit()
        print("✅ تم إضافة عمود image_file_id")
    conn.close()


def get_db():
    return sqlite3.connect(DB_PATH)


def log_admin_action(admin_id, action, target_type, target_id, details=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO admin_logs (admin_id, action, target_type, target_id, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (admin_id, action, target_type, str(target_id), details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_setting(key, default=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                   (key, value, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_user_count():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_or_create_user(user_id, username, first_name, last_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, join_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, join_date))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user


def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def update_user_balance(user_id, amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def ban_user(user_id, banned=1):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (banned, user_id))
    conn.commit()
    conn.close()


def get_all_users(page=0, per_page=20):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY join_date DESC LIMIT ? OFFSET ?", (per_page, page * per_page))
    users = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    return users, total


def search_users(query):
    conn = get_db()
    cursor = conn.cursor()
    like = f"%{query}%"
    cursor.execute("SELECT * FROM users WHERE user_id = ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ?",
                   (query, like, like, like))
    users = cursor.fetchall()
    conn.close()
    return users


def get_user_orders_count(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_user_total_spent(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE user_id = ? AND status = 'completed'", (user_id,))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total


def get_products(page=0, per_page=5, category=None, active_only=True):
    conn = get_db()
    cursor = conn.cursor()
    if category:
        if active_only:
            cursor.execute("SELECT COUNT(*) FROM products WHERE category = ? AND is_active = 1", (category,))
            total = cursor.fetchone()[0]
            cursor.execute("SELECT * FROM products WHERE category = ? AND is_active = 1 ORDER BY display_order LIMIT ? OFFSET ?",
                           (category, per_page, page * per_page))
        else:
            cursor.execute("SELECT COUNT(*) FROM products WHERE category = ?", (category,))
            total = cursor.fetchone()[0]
            cursor.execute("SELECT * FROM products WHERE category = ? ORDER BY display_order LIMIT ? OFFSET ?",
                           (category, per_page, page * per_page))
    else:
        if active_only:
            cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY display_order LIMIT ? OFFSET ?",
                           (per_page, page * per_page))
        else:
            cursor.execute("SELECT COUNT(*) FROM products")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT * FROM products ORDER BY display_order LIMIT ? OFFSET ?",
                           (per_page, page * per_page))
    products = cursor.fetchall()
    conn.close()
    return products, total


def get_all_products(active_only=False):
    conn = get_db()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY display_order")
    else:
        cursor.execute("SELECT * FROM products ORDER BY display_order")
    products = cursor.fetchall()
    conn.close()
    return products


def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product


def add_product(name, price, stock, warranty, emoji, discount, features, category, requires_account=0, image_file_id=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(display_order) FROM products")
    max_order = cursor.fetchone()[0] or 0
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO products (name, price, stock, warranty, emoji, discount, features, category, display_order, requires_account, created_at, image_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, price, stock, warranty, emoji, discount, features, category, max_order + 1, requires_account, created_at, image_file_id))
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id


def update_product(product_id, field, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE products SET {field} = ? WHERE id = ?", (value, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def restore_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_active = 1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def reorder_product(product_id, new_order):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET display_order = ? WHERE id = ?", (new_order, product_id))
    conn.commit()
    conn.close()


def update_product_stock(product_id, quantity):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()


def increment_product_sales(product_id, quantity):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET sales_count = sales_count + ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()


def create_order(user_id, product_id, quantity, total_price, payment_method, client_email="", delivered_email="", delivered_password="", fawaterk_invoice_id="", coupon_code="", discount_amount=0):
    conn = get_db()
    cursor = conn.cursor()
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO orders (user_id, product_id, quantity, total_price, status, order_date, payment_method, client_email, delivered_email, delivered_password, fawaterk_invoice_id, coupon_code, discount_amount)
        VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, product_id, quantity, total_price, order_date, payment_method, client_email, delivered_email, delivered_password, fawaterk_invoice_id, coupon_code, discount_amount))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id


def get_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order


def update_order_status(order_id, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()


def update_order_notes(order_id, notes):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET admin_notes = ? WHERE id = ?", (notes, order_id))
    conn.commit()
    conn.close()


def get_user_orders(user_id, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, p.name FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.user_id = ? ORDER BY o.order_date DESC LIMIT ?
    ''', (user_id, limit))
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_orders(status=None, page=0, per_page=10):
    conn = get_db()
    cursor = conn.cursor()
    if status:
        cursor.execute('''
            SELECT o.*, p.name, u.username, u.first_name FROM orders o 
            JOIN products p ON o.product_id = p.id 
            JOIN users u ON o.user_id = u.user_id
            WHERE o.status = ? ORDER BY o.order_date DESC LIMIT ? OFFSET ?
        ''', (status, per_page, page * per_page))
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = ?", (status,))
    else:
        cursor.execute('''
            SELECT o.*, p.name, u.username, u.first_name FROM orders o 
            JOIN products p ON o.product_id = p.id 
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC LIMIT ? OFFSET ?
        ''', (per_page, page * per_page))
        cursor.execute("SELECT COUNT(*) FROM orders")
    orders = cursor.fetchall()
    total = cursor.fetchone()[0]
    conn.close()
    return orders, total


def search_orders(query):
    conn = get_db()
    cursor = conn.cursor()
    like = f"%{query}%"
    cursor.execute('''
        SELECT o.*, p.name, u.username, u.first_name FROM orders o 
        JOIN products p ON o.product_id = p.id 
        JOIN users u ON o.user_id = u.user_id
        WHERE o.id = ? OR p.name LIKE ? OR u.username LIKE ? OR u.first_name LIKE ? OR o.client_email LIKE ?
        ORDER BY o.order_date DESC LIMIT 20
    ''', (query, like, like, like, like))
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_pending_orders():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, p.name, u.username, u.first_name FROM orders o 
        JOIN products p ON o.product_id = p.id 
        JOIN users u ON o.user_id = u.user_id
        WHERE o.status = 'pending' ORDER BY o.order_date DESC
    ''')
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_pending_recharges():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, u.username, u.first_name FROM recharges r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.status = 'pending' ORDER BY r.request_date DESC
    ''')
    recharges = cursor.fetchall()
    conn.close()
    return recharges


def get_recharges(status=None, page=0, per_page=10):
    conn = get_db()
    cursor = conn.cursor()
    if status:
        cursor.execute('''
            SELECT r.*, u.username, u.first_name FROM recharges r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.status = ? ORDER BY r.request_date DESC LIMIT ? OFFSET ?
        ''', (status, per_page, page * per_page))
        cursor.execute("SELECT COUNT(*) FROM recharges WHERE status = ?", (status,))
    else:
        cursor.execute('''
            SELECT r.*, u.username, u.first_name FROM recharges r
            JOIN users u ON r.user_id = u.user_id
            ORDER BY r.request_date DESC LIMIT ? OFFSET ?
        ''', (per_page, page * per_page))
        cursor.execute("SELECT COUNT(*) FROM recharges")
    recharges = cursor.fetchall()
    total = cursor.fetchone()[0]
    conn.close()
    return recharges, total


def create_recharge(user_id, amount, phone_number, fawaterk_invoice_id=""):
    conn = get_db()
    cursor = conn.cursor()
    request_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO recharges (user_id, amount, phone_number, status, request_date, fawaterk_invoice_id)
        VALUES (?, ?, ?, 'pending', ?, ?)
    ''', (user_id, amount, phone_number, request_date, fawaterk_invoice_id))
    recharge_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return recharge_id


def get_recharge(recharge_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recharges WHERE id = ?", (recharge_id,))
    recharge = cursor.fetchone()
    conn.close()
    return recharge


def update_recharge_status(recharge_id, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE recharges SET status = ? WHERE id = ?", (status, recharge_id))
    conn.commit()
    conn.close()


def is_admin(user_id):
    return user_id in ADMIN_IDS


def grant_admin_session(user_id, role="admin"):
    conn = get_db()
    cursor = conn.cursor()
    granted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT OR REPLACE INTO admin_sessions (user_id, is_active, granted_at, role)
        VALUES (?, 1, ?, ?)
    ''', (user_id, granted_at, role))
    conn.commit()
    conn.close()


def revoke_admin_session(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admin_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def is_admin_session_active(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM admin_sessions WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None and result[0] == 1


def get_admin_role(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM admin_sessions WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "admin"


def add_admin(user_id, role="moderator"):
    global ADMIN_IDS
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
    grant_admin_session(user_id, role)


def remove_admin(user_id):
    global ADMIN_IDS
    if user_id in ADMIN_IDS and user_id != 5811814277:
        ADMIN_IDS.remove(user_id)
    revoke_admin_session(user_id)


# ==================== COUPONS ====================
def create_coupon(code, discount_percent, max_uses, created_by, expires_at=None, min_order_amount=0):
    conn = get_db()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO coupons (code, discount_percent, max_uses, created_by, created_at, expires_at, min_order_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (code.upper(), discount_percent, max_uses, created_by, created_at, expires_at, min_order_amount))
    conn.commit()
    conn.close()


def get_coupon(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code.upper(),))
    coupon = cursor.fetchone()
    conn.close()
    return coupon


def use_coupon(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE coupons SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
    conn.commit()
    conn.close()


def get_all_coupons():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons ORDER BY created_at DESC")
    coupons = cursor.fetchall()
    conn.close()
    return coupons


def delete_coupon(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM coupons WHERE code = ?", (code.upper(),))
    conn.commit()
    conn.close()


# ==================== CATEGORIES ====================
def get_all_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY display_order")
    cats = cursor.fetchall()
    conn.close()
    return cats


def add_category(name, emoji="📁"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(display_order) FROM categories")
    max_order = cursor.fetchone()[0] or 0
    try:
        cursor.execute("INSERT INTO categories (name, emoji, display_order) VALUES (?, ?, ?)",
                       (name, emoji, max_order + 1))
        conn.commit()
        cat_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cat_id = None
    conn.close()
    return cat_id


def delete_category(cat_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET is_active = 0 WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


# ==================== FAWATERK API ====================
async def get_fawaterk_token():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FAWATERK_API_BASE}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": FAWATERK_CLIENT_ID,
                "client_secret": FAWATERK_CLIENT_SECRET,
            },
            timeout=30.0
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("access_token")

async def create_fawaterk_invoice(token, amount, description, user, payment_method_id=""):
    async with httpx.AsyncClient() as client:
        payload = {
            "cartTotal": amount,
            "currency": "EGP",
            "customer": {
                "first_name": f"User{user.id}",
                "last_name": "Client",
                "email": f"user{user.id}@Tamm Shop.bot",
                "phone": get_setting("wallet_number", WALLET_NUMBER)
            },
            "redirectionUrls": {
                "successUrl": "https://t.me/Tamm ShopBot",
                "failUrl": "https://t.me/Tamm ShopBot",
                "pendingUrl": "https://t.me/Tamm ShopBot"
            },
            "cartItems": [
                {
                    "name": description,
                    "price": amount,
                    "quantity": 1
                }
            ]
        }
        if payment_method_id:
            payload["payment_method_id"] = payment_method_id

        resp = await client.post(
            f"{FAWATERK_API_BASE}/api/v3/createTransaction",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30.0
        )
        if resp.status_code != 200:
            print(f"Fawaterk Error Response: {resp.text}")
        resp.raise_for_status()
        return resp.json()

async def check_fawaterk_invoice(token, invoice_id):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{FAWATERK_API_BASE}/api/v2/invoice/{invoice_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()


# ==================== ENHANCED KEYBOARDS ====================
def main_menu_keyboard(user_id=None):
    """كيبورد سفلي مبسط — زرين فقط"""
    rows = [
        ["🏠 الرئيسية", "🛍 المنتجات"],
    ]
    if user_id and (is_admin(user_id) or is_admin_session_active(user_id)):
        rows.append(["🔐 لوحة التحكم المتقدمة"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def main_inline_menu_keyboard(user_id):
    """القائمة الرئيسية التفاعلية (Inline)"""
    buttons = [
        [InlineKeyboardButton("🛍 تصفح المنتجات", callback_data="browse_products")],
        [InlineKeyboardButton("🛒 طلباتي", callback_data="my_orders"),
         InlineKeyboardButton("💰 محفظتي", callback_data="my_wallet")],
        [InlineKeyboardButton("💳 شحن رصيد", callback_data="recharge_balance"),
         InlineKeyboardButton("🎟 الكوبونات", callback_data="my_coupons")],
        [InlineKeyboardButton("💬 الدعم الفني", callback_data="support"),
         InlineKeyboardButton("📖 شرح البوت", callback_data="tutorial")],
    ]
    return InlineKeyboardMarkup(buttons)


def wallet_inline_keyboard():
    """أزرار تفاعلية لطرق الشحن في المحفظة"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏦 محفظة إلكترونية (يدوي)", callback_data="recharge_manual_wallet")],
        [InlineKeyboardButton("🅱️ بينانس (USDT)", callback_data="recharge_binance")],
        [InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="main_menu")],
    ])


def admin_dashboard_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 إدارة المنتجات", callback_data="admin_products_menu")],
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users_menu")],
        [InlineKeyboardButton("📦 الطلبيات", callback_data="admin_orders_menu")],
        [InlineKeyboardButton("💳 شحن الرصيد", callback_data="admin_recharges_menu")],
        [InlineKeyboardButton("🎟 الكوبونات", callback_data="admin_coupons_menu")],
        [InlineKeyboardButton("📂 الفئات", callback_data="admin_categories_menu")],
        [InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="admin_settings_menu")],
        [InlineKeyboardButton("📢 إرسال إشعار", callback_data="admin_broadcast_menu")],
        [InlineKeyboardButton("📊 الإحصائيات المتقدمة", callback_data="admin_stats_advanced")],
        [InlineKeyboardButton("📋 سجل العمليات", callback_data="admin_logs_menu")],
        [InlineKeyboardButton("💾 نسخ احتياطي", callback_data="admin_backup")],
        [InlineKeyboardButton("🚪 خروج من لوحة التحكم", callback_data="admin_exit")],
    ])


def admin_products_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة منتج", callback_data="admin_add_product")],
        [InlineKeyboardButton("📋 قائمة المنتجات", callback_data="admin_list_products")],
        [InlineKeyboardButton("✏️ تعديل منتج", callback_data="admin_edit_product")],
        [InlineKeyboardButton("🗑️ حذف/استرجاع منتج", callback_data="admin_delete_product")],
        [InlineKeyboardButton("📂 إدارة الفئات", callback_data="admin_categories_menu")],
        [InlineKeyboardButton("📊 أكثر المنتجات مبيعاً", callback_data="admin_top_products")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def admin_users_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_list_users")],
        [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="admin_search_user")],
        [InlineKeyboardButton("💰 تعديل رصيد مستخدم", callback_data="admin_edit_balance")],
        [InlineKeyboardButton("🚫 حظر/فك حظر", callback_data="admin_ban_user")],
        [InlineKeyboardButton("📊 إحصائيات المستخدمين", callback_data="admin_users_stats")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def admin_orders_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 الطلبات المعلقة", callback_data="admin_pending_orders")],
        [InlineKeyboardButton("✅ الطلبات المكتملة", callback_data="admin_completed_orders")],
        [InlineKeyboardButton("❌ الطلبات المرفوضة", callback_data="admin_rejected_orders")],
        [InlineKeyboardButton("🔍 بحث عن طلب", callback_data="admin_search_order")],
        [InlineKeyboardButton("📊 إحصائيات الطلبات", callback_data="admin_orders_stats")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def admin_recharges_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ طلبات الشحن المعلقة", callback_data="admin_pending_recharges")],
        [InlineKeyboardButton("✅ طلبات الشحن المكتملة", callback_data="admin_completed_recharges")],
        [InlineKeyboardButton("❌ طلبات الشحن المرفوضة", callback_data="admin_rejected_recharges")],
        [InlineKeyboardButton("📊 إحصائيات الشحن", callback_data="admin_recharges_stats")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def admin_coupons_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إنشاء كوبون", callback_data="admin_add_coupon")],
        [InlineKeyboardButton("📋 قائمة الكوبونات", callback_data="admin_list_coupons")],
        [InlineKeyboardButton("🗑️ حذف كوبون", callback_data="admin_delete_coupon")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def admin_settings_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 تعديل رقم المحفظة", callback_data="admin_set_wallet")],
        [InlineKeyboardButton("🅱️ تعديل عنوان USDT", callback_data="admin_set_usdt")],
        [InlineKeyboardButton("💬 تعديل يوزر الدعم", callback_data="admin_set_support")],
        [InlineKeyboardButton("🏷 تعديل اسم البوت", callback_data="admin_set_botname")],
        [InlineKeyboardButton("📩 تعديل رسالة الترحيب", callback_data="admin_set_welcome")],
        [InlineKeyboardButton("🔧 وضع الصيانة", callback_data="admin_maintenance")],
        [InlineKeyboardButton("💱 تعديل سعر الدولار", callback_data="admin_set_usd_rate")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def admin_broadcast_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 رسالة للجميع", callback_data="admin_broadcast_all")],
        [InlineKeyboardButton("👤 رسالة لمستخدم محدد", callback_data="admin_broadcast_user")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def admin_logs_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 آخر 20 عملية", callback_data="admin_logs_20")],
        [InlineKeyboardButton("📋 آخر 50 عملية", callback_data="admin_logs_50")],
        [InlineKeyboardButton("🔍 بحث في السجل", callback_data="admin_logs_search")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")],
    ])


def products_inline_keyboard(products, page, total):
    buttons = []
    for p in products:
        stock_emoji = "✅" if p[3] > 5 else "⚠️" if p[3] > 0 else "❌"
        btn_text = f"{p[5]} {p[1]} | {p[2]:.0f} ج.م | {stock_emoji} {p[3]}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"product_{p[0]}")])

    total_pages = (total + 4) // 5
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"page_{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"page_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def product_detail_keyboard(product_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 شراء الآن", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("⬅️ رجوع للمتجر", callback_data="back_to_products")],
    ])


def quantity_keyboard(product_id, stock):
    quantities = [1, 2, 3, 5]
    buttons = []
    row = []
    for q in quantities:
        if q <= stock:
            row.append(InlineKeyboardButton(f"{q} 📦", callback_data=f"qty_{product_id}_{q}"))
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🎯 كمية مخصصة", callback_data=f"custom_qty_{product_id}")])
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"product_{product_id}")])
    return InlineKeyboardMarkup(buttons)


def payment_methods_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 ادفع من رصيدك", callback_data="pay_wallet")],
        [InlineKeyboardButton("📱 فودافون كاش (آلي)", callback_data="pay_vodafone")],
        [InlineKeyboardButton("💳 انستا باي (آلي)", callback_data="pay_instapay")],
        [InlineKeyboardButton("🅱️ بينانس (يدوي)", callback_data="pay_binance")],
        [InlineKeyboardButton("🎟 تطبيق كوبون خصم", callback_data="apply_coupon")],
        [InlineKeyboardButton("📥 شحن رصيد", callback_data="recharge")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_summary")],
    ])


def admin_order_notification_keyboard(order_id, requires_account=0):
    if requires_account == 1:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 تسليم حساب", callback_data=f"admin_deliver_{order_id}")],
            [InlineKeyboardButton("❌ رفض الطلب", callback_data=f"admin_reject_order_{order_id}")],
            [InlineKeyboardButton("📝 إضافة ملاحظة", callback_data=f"admin_note_order_{order_id}")]
        ])
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأكيد الطلب", callback_data=f"admin_confirm_order_{order_id}"),
            InlineKeyboardButton("❌ رفض الطلب", callback_data=f"admin_reject_order_{order_id}")
        ],
        [InlineKeyboardButton("📝 إضافة ملاحظة", callback_data=f"admin_note_order_{order_id}")]
    ])


def admin_recharge_notification_keyboard(recharge_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأكيد الشحن", callback_data=f"admin_confirm_recharge_{recharge_id}"),
            InlineKeyboardButton("❌ رفض الشحن", callback_data=f"admin_reject_recharge_{recharge_id}")
        ],
        [InlineKeyboardButton("📝 إضافة ملاحظة", callback_data=f"admin_note_recharge_{recharge_id}")]
    ])


# ==================== ENHANCED ADMIN NOTIFICATIONS ====================
async def notify_admins_order(context, order_id, user, product, quantity, total_price, payment_method, client_email=""):
    safe_name = html.escape(user.first_name) if user.first_name else "مستخدم"
    user_mention = f"@{html.escape(user.username)}" if user.username else f'<a href="tg://user?id={user.id}">{safe_name}</a>'
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    requires_account = product[10] if len(product) > 10 else 0
    product_type = "🎁 أكونت جاهز" if requires_account == 1 else "🔧 تفعيل على أكونت شخصي"

    text = (
        f"🔔 طلب جديد (بانتظار المراجعة)!\n\n"
        f"👤 المستخدم: {user_mention}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🛍 المنتج: {html.escape(product[1])}\n"
        f"🏷️ النوع: {product_type}\n"
        f"🔢 الكمية: {quantity}\n"
        f"💰 الإجمالي: {total_price:.0f} ج.م\n"
        f"💳 طريقة الدفع: {html.escape(payment_method)}\n"
    )
    if client_email:
        text += f"📧 إيميل العميل: <code>{html.escape(client_email)}</code>\n"
    text += f"📅 التاريخ: {date_str}"

    for admin_id in ADMIN_IDS:
        try:
            kb = admin_order_notification_keyboard(order_id, requires_account)
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

async def notify_admins_recharge(context, user, amount, sender_info, recharge_id):
    safe_name = html.escape(user.first_name) if user.first_name else "مستخدم"
    user_mention = f"@{html.escape(user.username)}" if user.username else f'<a href="tg://user?id={user.id}">{safe_name}</a>'
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = (
        f"💳 طلب شحن رصيد جديد (بانتظار التأكيد)!\n\n"
        f"👤 المستخدم: {user_mention}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"💰 المبلغ: {amount:.0f} ج.م\n"
        f"📱 تفاصيل التحويل: <code>{html.escape(sender_info)}</code>\n"
        f"📅 التاريخ: {date_str}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
                reply_markup=admin_recharge_notification_keyboard(recharge_id)
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")


# ==================== MAIN HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user

    u = get_user(user.id)
    if u and u[7] == 1:
        await update.message.reply_text("🚫 تم حظرك من استخدام البوت. تواصل مع الدعم.")
        return

    if get_setting("maintenance_mode") == "1" and not is_admin(user.id):
        await update.message.reply_text("🔧 البوت في وضع الصيانة حالياً. جرب تاني بعدين.")
        return

    user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    user_count = get_user_count()
    balance = user_data[4] if user_data[4] else 0
    bot_name = get_setting("bot_name", "Tamm Shop")

    text = (
        f"👥 {user_count:,} مستخدم\n\n"
        f"✨ متجر {bot_name} • تسليم فوري\n"
        f"🏛 أهلاً بيك يا {user.first_name or 'عزيزي'} في {bot_name}\n\n"
        f"🛍 رصيدك الحالي: {balance:.0f} ج.م\n\n"
        f"👇 اختار من القائمة اللي تحت"
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(user.id))


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية التفاعلية (Inline)"""
    user = update.effective_user
    user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    balance = user_data[4] if user_data[4] else 0
    order_count = get_user_orders_count(user.id)
    bot_name = get_setting("bot_name", "Tamm Shop")

    text = (
        f"*🏠 القائمة الرئيسية*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👋 مرحباً *{user.first_name or 'عزيزي'}*\n"
        f"🏪 *{bot_name}* — تسوق ذكي وتسليم فوري\n\n"
        f"💰 *رصيدك:* `{balance:.0f}` ج.م\n"
        f"🛒 *طلباتك:* `{order_count}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👇 *اختر ما تريد:*"
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_inline_menu_keyboard(user.id)
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_inline_menu_keyboard(user.id)
        )


async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """واجهة المحفظة المحسنة مع تصميم أنيق وأزرار تفاعلية"""
    user = update.effective_user
    user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    balance = user_data[4] if user_data[4] else 0
    spent = get_user_total_spent(user.id)
    order_count = get_user_orders_count(user.id)

    text = (
        f"*💰 محفظتي*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 *{user.first_name or 'عزيزي'}*\n\n"
        f"💵 *الرصيد الحالي:*\n"
        f"`{balance:.0f}` *ج.م* 💎\n\n"
        f"📊 *إحصائيات سريعة:*\n"
        f"• الطلبات: `{order_count}`\n"
        f"• إجمالي المشتريات: `{spent:.0f}` ج.م\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💳 *اختر طريقة الشحن:*"
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=wallet_inline_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=wallet_inline_keyboard()
        )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text("❌ استخدم: /admin [الكود السري]", reply_markup=main_menu_keyboard(user.id))
        return

    provided_code = args[0]

    if provided_code != ADMIN_SECRET and not is_admin(user.id):
        await update.message.reply_text("❌ كود غير صحيح!", reply_markup=main_menu_keyboard(user.id))
        return

    if is_admin(user.id) or provided_code == ADMIN_SECRET:
        grant_admin_session(user.id, "super_admin" if is_admin(user.id) else "admin")
        context.user_data["admin_mode"] = True
        context.user_data["admin_state"] = "menu"

        text = (
            f"🔐 تم تسجيل الدخول كأدمن!\n\n"
            f"👤 مرحباً {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"⚡️ الدور: {get_admin_role(user.id)}\n\n"
            f"👇 اختار الإجراء المطلوب:"
        )
        await update.message.reply_text(text, reply_markup=admin_dashboard_keyboard())

async def exit_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    revoke_admin_session(user.id)
    context.user_data.clear()
    await update.message.reply_text(
        "🚪 تم تسجيل الخروج من لوحة التحكم.\n\n👋 رجعت للوضع العادي.",
        reply_markup=main_menu_keyboard(user.id)
    )


# ==================== PRODUCTS ADMIN HANDLERS ====================
async def admin_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🛍 إدارة المنتجات\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_products_menu_keyboard()
    )

async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = get_all_products(active_only=False)
    if not products:
        await query.edit_message_text("❌ مفيش منتجات!", reply_markup=admin_products_menu_keyboard())
        return
    text = "📋 قائمة المنتجات:\n\n"
    for p in products:
        status = "✅" if p[11] == 1 else "🚫"
        has_img = "🖼️" if p[13] else ""
        text += f"{status} {has_img} {p[5]} {p[1]} — {p[2]:.0f}ج — 📦{p[3]} — 🏷️{p[8]}\n"
    await query.edit_message_text(text, reply_markup=admin_products_menu_keyboard())

async def admin_add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "add_name"
    context.user_data["temp_product"] = {}
    await query.edit_message_text(
        "➕ إضافة منتج جديد\n\nالخطوة 1/8\n📝 ارسل اسم المنتج:"
    )

async def admin_edit_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = get_all_products(active_only=False)
    if not products:
        await query.edit_message_text("❌ مفيش منتجات!")
        return
    buttons = []
    for p in products:
        status = "✅" if p[11] == 1 else "🚫"
        buttons.append([InlineKeyboardButton(f"{status} {p[5]} {p[1]}", callback_data=f"admin_edit_select_{p[0]}")])
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_products_menu")])
    await query.edit_message_text("✏️ اختار المنتج اللي عايز تعدله:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_delete_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = get_all_products(active_only=False)
    if not products:
        await query.edit_message_text("❌ مفيش منتجات!")
        return
    buttons = []
    for p in products:
        action = "🗑️ إخفاء" if p[11] == 1 else "♻️ استرجاع"
        buttons.append([InlineKeyboardButton(f"{action} {p[5]} {p[1]}", callback_data=f"admin_toggle_product_{p[0]}")])
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_products_menu")])
    await query.edit_message_text("🗑️ اختار المنتج:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_toggle_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[3])
    product = get_product(product_id)
    if product[11] == 1:
        delete_product(product_id)
        await query.edit_message_text(f"🗑️ تم إخفاء المنتج: {product[1]}", reply_markup=admin_products_menu_keyboard())
    else:
        restore_product(product_id)
        await query.edit_message_text(f"♻️ تم استرجاع المنتج: {product[1]}", reply_markup=admin_products_menu_keyboard())

async def admin_top_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, sales_count, price FROM products ORDER BY sales_count DESC LIMIT 10")
    top = cursor.fetchall()
    conn.close()
    if not top:
        await query.edit_message_text("❌ مفيش بيانات مبيعات!")
        return
    text = "📊 أكثر 10 منتجات مبيعاً:\n\n"
    for i, p in enumerate(top, 1):
        revenue = p[1] * p[2]
        text += f"{i}. {p[0]} — 🔥 {p[1]} مبيعة — 💰 {revenue:.0f}ج\n"
    await query.edit_message_text(text, reply_markup=admin_products_menu_keyboard())


# ==================== USERS ADMIN HANDLERS ====================
async def admin_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👥 إدارة المستخدمين\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_users_menu_keyboard()
    )

async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = context.user_data.get("users_page", 0)
    users, total = get_all_users(page, 10)
    if not users:
        await query.edit_message_text("❌ مفيش مستخدمين!")
        return
    text = f"👥 المستخدمون (الصفحة {page+1}):\n\n"
    for u in users:
        ban = "🚫" if u[7] == 1 else "✅"
        spent = get_user_total_spent(u[0])
        text += f"{ban} ID:{u[0]} | {u[2] or u[3] or 'N/A'} | 💰{u[4]:.0f}ج | 🧾{get_user_orders_count(u[0])} | 💵{spent:.0f}ج\n"

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"admin_users_page_{page-1}"))
    if (page + 1) * 10 < total:
        buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"admin_users_page_{page+1}"))
    nav = [buttons] if buttons else []
    nav.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_users_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(nav))

async def admin_search_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "search_user"
    await query.edit_message_text("🔍 ارسل ID المستخدم أو يوزر أو اسم للبحث:")

async def admin_edit_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "edit_balance_user_id"
    await query.edit_message_text("💰 ارسل ID المستخدم اللي عايز تعدل رصيده:")

async def admin_ban_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "ban_user_id"
    await query.edit_message_text("🚫 ارسل ID المستخدم اللي عايز تحظره/تفك حظره:")

async def admin_users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date >= date('now', '-7 days')")
    new_week = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date >= date('now', '-30 days')")
    new_month = cursor.fetchone()[0]
    conn.close()
    text = (
        f"📊 إحصائيات المستخدمين\n\n"
        f"👥 إجمالي المستخدمين: {total}\n"
        f"🚫 المحظورين: {banned}\n"
        f"💰 إجمالي الأرصدة: {total_balance:.0f} ج.م\n"
        f"📈 جديد هذا الأسبوع: {new_week}\n"
        f"📈 جديد هذا الشهر: {new_month}"
    )
    await query.edit_message_text(text, reply_markup=admin_users_menu_keyboard())


# ==================== ORDERS ADMIN HANDLERS ====================
async def admin_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📦 الطلبيات\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_orders_menu_keyboard()
    )

async def admin_pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    orders = get_pending_orders()
    if not orders:
        await query.edit_message_text("✅ مفيش طلبات معلقة حالياً!", reply_markup=admin_orders_menu_keyboard())
        return
    await query.edit_message_text("📦 جاري إرسال الطلبات المعلقة...")
    for o in orders:
        product = get_product(o[2])
        requires_account = product[10] if len(product) > 10 else 0
        product_type = "🎁 أكونت جاهز" if requires_account == 1 else "🔧 تفعيل على أكونت"
        user_name = o[16] or o[17] or f"ID: {o[1]}"
        client_email = o[8] if len(o) > 8 and o[8] else ""
        fawaterk_info = f"\n⚡ فاتورة: {o[11]}" if len(o) > 11 and o[11] else ""
        coupon_info = f"\n🎟 كوبون: {o[13]}" if len(o) > 13 and o[13] else ""

        text = (
            f"📦 طلب معلق\n\n"
            f"🆔 #{o[0]}\n"
            f"👤 {user_name}\n"
            f"🔢 {o[3]} قطعة | {o[4]:.0f} ج.م\n"
            f"💳 {o[7]}{fawaterk_info}{coupon_info}\n"
            f"🏷️ النوع: {product_type}\n"
        )
        if client_email:
            text += f"📧 إيميل العميل: {client_email}\n"
        if len(o) > 12 and o[12]:
            text += f"📝 ملاحظات: {o[12]}\n"
        text += f"📅 {o[6]}"

        if requires_account == 1:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 تسليم حساب", callback_data=f"admin_deliver_{o[0]}")],
                [InlineKeyboardButton("❌ رفض الطلب", callback_data=f"admin_reject_order_{o[0]}")],
                [InlineKeyboardButton("📝 ملاحظة", callback_data=f"admin_note_order_{o[0]}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_orders_menu")]
            ])
        else:
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تأكيد", callback_data=f"admin_confirm_order_{o[0]}"),
                    InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_order_{o[0]}")
                ],
                [InlineKeyboardButton("📝 ملاحظة", callback_data=f"admin_note_order_{o[0]}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_orders_menu")]
            ])

        try:
            await context.bot.send_message(chat_id=query.message.chat_id, text=text, reply_markup=kb)
        except Exception as e:
            logger.error(f"Failed to send pending order: {e}")

async def admin_completed_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = context.user_data.get("completed_orders_page", 0)
    orders, total = get_orders("completed", page, 5)
    if not orders:
        await query.edit_message_text("❌ مفيش طلبات مكتملة!", reply_markup=admin_orders_menu_keyboard())
        return
    text = f"✅ الطلبات المكتملة (صفحة {page+1}):\n\n"
    for o in orders:
        text += f"🆔#{o[0]} | {o[12]} | {o[3]}قطعة | {o[4]:.0f}ج | 👤{o[13] or o[14]}\n"
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"admin_completed_page_{page-1}"))
    if (page + 1) * 5 < total:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"admin_completed_page_{page+1}"))
    nav = [buttons] if buttons else []
    nav.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_orders_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(nav))

async def admin_rejected_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = context.user_data.get("rejected_orders_page", 0)
    orders, total = get_orders("rejected", page, 5)
    if not orders:
        await query.edit_message_text("❌ مفيش طلبات مرفوضة!", reply_markup=admin_orders_menu_keyboard())
        return
    text = f"❌ الطلبات المرفوضة (صفحة {page+1}):\n\n"
    for o in orders:
        text += f"🆔#{o[0]} | {o[12]} | {o[3]}قطعة | {o[4]:.0f}ج | 👤{o[13] or o[14]}\n"
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"admin_rejected_page_{page-1}"))
    if (page + 1) * 5 < total:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"admin_rejected_page_{page+1}"))
    nav = [buttons] if buttons else []
    nav.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_orders_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(nav))

async def admin_search_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "search_order"
    await query.edit_message_text("🔍 ارسل رقم الطلب أو اسم المنتج أو اسم المستخدم للبحث:")

async def admin_orders_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'rejected'")
    rejected = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed'")
    revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'pending'")
    pending_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT AVG(total_price) FROM orders WHERE status = 'completed'")
    avg_order = cursor.fetchone()[0] or 0
    conn.close()
    text = (
        f"📊 إحصائيات الطلبات\n\n"
        f"📦 إجمالي الطلبات: {total}\n"
        f"✅ المكتملة: {completed}\n"
        f"⏳ المعلقة: {pending}\n"
        f"❌ المرفوضة: {rejected}\n"
        f"💰 إيرادات مكتملة: {revenue:.0f} ج.م\n"
        f"⏳ إيرادات معلقة: {pending_revenue:.0f} ج.م\n"
        f"📊 متوسط قيمة الطلب: {avg_order:.0f} ج.م"
    )
    await query.edit_message_text(text, reply_markup=admin_orders_menu_keyboard())


# ==================== RECHARGES ADMIN HANDLERS ====================
async def admin_recharges_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💳 شحن الرصيد\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_recharges_menu_keyboard()
    )

async def admin_pending_recharges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    recharges = get_pending_recharges()
    if not recharges:
        await query.edit_message_text("✅ مفيش طلبات شحن معلقة!", reply_markup=admin_recharges_menu_keyboard())
        return
    text = "💳 طلبات الشحن المعلقة:\n\n"
    for r in recharges:
        user_name = r[9] or r[10] or f"ID: {r[1]}"
        fawaterk_info = f"\n⚡ فاتورة ID: {r[6]}" if len(r) > 6 and r[6] else ""
        text += (
            f"🆔 #{r[0]} | {r[2]:.0f} ج.م\n"
            f"👤 {user_name}\n"
            f"📱 {r[3]}{fawaterk_info}\n"
            f"📅 {r[4]}\n---\n"
        )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_recharges_menu")]
    ]))

async def admin_completed_recharges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = context.user_data.get("completed_recharges_page", 0)
    recharges, total = get_recharges("completed", page, 5)
    if not recharges:
        await query.edit_message_text("❌ مفيش طلبات شحن مكتملة!", reply_markup=admin_recharges_menu_keyboard())
        return
    text = f"✅ طلبات الشحن المكتملة (صفحة {page+1}):\n\n"
    for r in recharges:
        text += f"🆔#{r[0]} | {r[2]:.0f}ج | 👤{r[7] or r[8]}\n"
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"admin_rech_comp_page_{page-1}"))
    if (page + 1) * 5 < total:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"admin_rech_comp_page_{page+1}"))
    nav = [buttons] if buttons else []
    nav.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_recharges_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(nav))

async def admin_rejected_recharges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = context.user_data.get("rejected_recharges_page", 0)
    recharges, total = get_recharges("rejected", page, 5)
    if not recharges:
        await query.edit_message_text("❌ مفيش طلبات شحن مرفوضة!", reply_markup=admin_recharges_menu_keyboard())
        return
    text = f"❌ طلبات الشحن المرفوضة (صفحة {page+1}):\n\n"
    for r in recharges:
        text += f"🆔#{r[0]} | {r[2]:.0f}ج | 👤{r[7] or r[8]}\n"
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"admin_rech_rej_page_{page-1}"))
    if (page + 1) * 5 < total:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"admin_rech_rej_page_{page+1}"))
    nav = [buttons] if buttons else []
    nav.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_recharges_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(nav))

async def admin_recharges_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recharges")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM recharges WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM recharges WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(amount) FROM recharges WHERE status = 'completed'")
    total_amount = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM recharges WHERE status = 'pending'")
    pending_amount = cursor.fetchone()[0] or 0
    conn.close()
    text = (
        f"📊 إحصائيات الشحن\n\n"
        f"💳 إجمالي الطلبات: {total}\n"
        f"✅ المكتملة: {completed}\n"
        f"⏳ المعلقة: {pending}\n"
        f"💰 إجمالي مكتمل: {total_amount:.0f} ج.م\n"
        f"⏳ معلق: {pending_amount:.0f} ج.م"
    )
    await query.edit_message_text(text, reply_markup=admin_recharges_menu_keyboard())


# ==================== COUPONS ADMIN HANDLERS ====================
async def admin_coupons_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎟 إدارة الكوبونات\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_coupons_menu_keyboard()
    )

async def admin_add_coupon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "coupon_code"
    context.user_data["temp_coupon"] = {}
    await query.edit_message_text(
        "🎟 إنشاء كوبون جديد\n\nالخطوة 1/4\n📝 ارسل كود الكوبون (مثال: SUMMER20):"
    )

async def admin_list_coupons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coupons = get_all_coupons()
    if not coupons:
        await query.edit_message_text("❌ مفيش كوبونات!", reply_markup=admin_coupons_menu_keyboard())
        return
    text = "📋 قائمة الكوبونات:\n\n"
    for c in coupons:
        status = "✅" if c[6] == 1 else "🚫"
        expired = "⌛ منتهي" if c[5] and c[5] < datetime.now().strftime("%Y-%m-%d") else ""
        text += f"{status} {c[0]} | 📉{c[1]}% | 🎯{c[3]}/{c[2]} | 🏷️{c[7]:.0f}ج {expired}\n"
    await query.edit_message_text(text, reply_markup=admin_coupons_menu_keyboard())

async def admin_delete_coupon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coupons = get_all_coupons()
    if not coupons:
        await query.edit_message_text("❌ مفيش كوبونات!")
        return
    buttons = []
    for c in coupons:
        buttons.append([InlineKeyboardButton(f"🗑️ {c[0]} ({c[1]}%)", callback_data=f"admin_del_coupon_{c[0]}")])
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_coupons_menu")])
    await query.edit_message_text("🗑️ اختار الكوبون اللي عايز تمسحه:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_delete_coupon_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.split("_")[3]
    delete_coupon(code)
    await query.edit_message_text(f"🗑️ تم حذف الكوبون: {code}", reply_markup=admin_coupons_menu_keyboard())


# ==================== CATEGORIES ADMIN HANDLERS ====================
async def admin_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cats = get_all_categories()
    text = "📂 الفئات:\n\n"
    for c in cats:
        text += f"{c[2]} {c[1]} (ترتيب: {c[3]})\n"
    buttons = [
        [InlineKeyboardButton("➕ إضافة فئة", callback_data="admin_add_category")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_products_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def admin_add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "category_name"
    await query.edit_message_text("📂 إضافة فئة جديدة\n\nارسل اسم الفئة:")


def admin_categories_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة فئة", callback_data="admin_add_category")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_products_menu")]
    ])

# ==================== SETTINGS ADMIN HANDLERS ====================
async def admin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    wallet = get_setting("wallet_number")
    usdt = get_setting("usdt_address")
    support = get_setting("support_username")
    bot_name = get_setting("bot_name")
    usd_rate = get_setting("usd_rate")
    maintenance = "🔴 ON" if get_setting("maintenance_mode") == "1" else "🟢 OFF"
    text = (
        f"⚙️ إعدادات البوت\n\n"
        f"🏷️ الاسم: {bot_name}\n"
        f"💳 المحفظة: {wallet}\n"
        f"🅱️ USDT: {usdt[:20]}...\n"
        f"💬 الدعم: {support}\n"
        f"💱 سعر الدولار: {usd_rate}\n"
        f"🔧 صيانة: {maintenance}"
    )
    await query.edit_message_text(text, reply_markup=admin_settings_menu_keyboard())

async def admin_set_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "set_wallet"
    await query.edit_message_text("💳 ارسل رقم المحفظة الجديد:")

async def admin_set_usdt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "set_usdt"
    await query.edit_message_text("🅱️ ارسل عنوان USDT TRC20 الجديد:")

async def admin_set_support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "set_support"
    await query.edit_message_text("💬 ارسل يوزر الدعم الجديد (مثال: @Support):")

async def admin_set_botname_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "set_botname"
    await query.edit_message_text("🏷️ ارسل اسم البوت الجديد:")

async def admin_set_welcome_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "set_welcome"
    await query.edit_message_text("📩 ارسل رسالة الترحيب الجديدة:")

async def admin_maintenance_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = get_setting("maintenance_mode")
    new_val = "0" if current == "1" else "1"
    set_setting("maintenance_mode", new_val)
    status = "🔴 مفعل" if new_val == "1" else "🟢 معطل"
    await query.edit_message_text(f"🔧 وضع الصيانة: {status}", reply_markup=admin_settings_menu_keyboard())

async def admin_set_usd_rate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "set_usd_rate"
    await query.edit_message_text("💱 ارسل سعر الدولار الجديد (رقم فقط):")


# ==================== BROADCAST ADMIN HANDLERS ====================
async def admin_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📢 إرسال إشعارات\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_broadcast_menu_keyboard()
    )

async def admin_broadcast_all_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "broadcast_all"
    await query.edit_message_text("📢 ارسل الرسالة اللي عايز تبعتها لكل المستخدمين:\n(أرسل /cancel للإلغاء)")

async def admin_broadcast_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "broadcast_user_id"
    await query.edit_message_text("👤 ارسل ID المستخدم اللي عايز تبعتله رسالة:")


# ==================== LOGS ADMIN HANDLERS ====================
async def admin_logs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📋 سجل العمليات\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_logs_menu_keyboard()
    )

async def admin_logs_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    limit = int(query.data.split("_")[2])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    logs = cursor.fetchall()
    conn.close()
    if not logs:
        await query.edit_message_text("❌ مفيش سجلات!")
        return
    text = f"📋 آخر {limit} عملية:\n\n"
    for log in logs:
        text += f"🕐 {log[6]}\n👤 {log[1]} | {log[2]} | {log[3]}:{log[4]}\n📝 {log[5] or ''}\n---\n"
    await query.edit_message_text(text, reply_markup=admin_logs_menu_keyboard())

async def admin_logs_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "logs_search"
    await query.edit_message_text("🔍 ارسل كلمة للبحث في السجل:")


# ==================== BACKUP HANDLER ====================
async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as f:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=f,
                    filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                    caption="💾 نسخة احتياطية من قاعدة البيانات"
                )
            await query.edit_message_text("✅ تم إرسال النسخة الاحتياطية بنجاح!", reply_markup=admin_dashboard_keyboard())
        else:
            await query.edit_message_text("❌ ملف القاعدة غير موجود!")
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await query.edit_message_text(f"❌ حصل خطأ: {e}")


# ==================== ADVANCED STATS ====================
async def admin_stats_advanced(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
    active_products = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
    completed_orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    pending_orders = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed'")
    total_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'pending'")
    pending_revenue = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM recharges WHERE status = 'completed'")
    total_recharges = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM recharges WHERE status = 'completed'")
    completed_recharges = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balances = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM orders WHERE order_date >= date('now')")
    today_orders = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE order_date >= date('now') AND status = 'completed'")
    today_revenue = cursor.fetchone()[0] or 0

    conn.close()

    text = (
        f"📊 الإحصائيات المتقدمة\n\n"
        f"👥 المستخدمون: {total_users}\n"
        f"🛍 المنتجات: {active_products}/{total_products} نشطة\n"
        f"📦 الطلبات: {total_orders} (✅{completed_orders} | ⏳{pending_orders})\n"
        f"💰 إيرادات مكتملة: {total_revenue:.0f} ج.م\n"
        f"⏳ إيرادات معلقة: {pending_revenue:.0f} ج.م\n"
        f"📊 إجمالي الشحنات: {total_recharges:.0f} ج.م ({completed_recharges} عملية)\n"
        f"💳 إجمالي الأرصدة: {total_balances:.0f} ج.م\n"
        f"📈 طلبات اليوم: {today_orders} | 💰 {today_revenue:.0f} ج.م"
    )
    await query.edit_message_text(text, reply_markup=admin_dashboard_keyboard())


async def admin_back_to_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["admin_state"] = "menu"
    await query.edit_message_text(
        "🔐 لوحة تحكم الأدمن\n\n👇 اختار الإجراء المطلوب:",
        reply_markup=admin_dashboard_keyboard()
    )


# ==================== ORDER ACTIONS ====================
async def admin_confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[-1])
    order = get_order(order_id)
    admin_id = update.effective_user.id

    if not order or order[5] != "pending":
        await query.edit_message_text("❌ الطلب مش موجود أو اتعامل معاه قبل كده!")
        return

    product = get_product(order[2])
    requires_account = product[10] if len(product) > 10 else 0

    if requires_account == 1:
        context.user_data["admin_delivering_order"] = True
        context.user_data["admin_delivery_order_id"] = order_id
        context.user_data["admin_delivery_step"] = "email"
        await query.edit_message_text(
            f"📦 تسليم حساب جاهز — الطلب #{order_id}\n\n"
            f"🛍 {product[1]}\n"
            f"👤 المستخدم: {order[1]}\n\n"
            f"✍️ الخطوة 1/2 — ارسل الإيميل:"
        )
        return

    update_order_status(order_id, "completed")
    update_product_stock(order[2], order[3])
    increment_product_sales(order[2], order[3])
    log_admin_action(admin_id, "confirm_order", "order", order_id, f"Product: {product[1]}")

    client_email = order[8] if len(order) > 8 else ""
    try:
        msg = (
            f"✅ تم تأكيد طلبك وتفعيل الخدمة!\n\n"
            f"🛍 الطلب رقم: #{order_id}\n"
            f"💰 المبلغ: {order[4]:.0f} ج.م\n"
        )
        if client_email:
            msg += f"📧 تم التفعيل على الأكونت: <code>{html.escape(client_email)}</code>\n"
        msg += "\n🎉 استمتع بالخدمة!"
        await context.bot.send_message(chat_id=order[1], text=msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify user {order[1]}: {e}")

    await query.edit_message_text(f"✅ تم تأكيد الطلب #{order_id}")

async def admin_deliver_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[-1])
    order = get_order(order_id)
    if not order or order[5] != "pending":
        await query.edit_message_text("❌ الطلب مش موجود أو اتعامل معاه قبل كده!")
        return
    product = get_product(order[2])
    context.user_data["admin_delivering_order"] = True
    context.user_data["admin_delivery_order_id"] = order_id
    context.user_data["admin_delivery_step"] = "email"
    await query.edit_message_text(
        f"📦 تسليم حساب جاهز — الطلب #{order_id}\n\n"
        f"🛍 {product[1]}\n"
        f"👤 المستخدم: {order[1]}\n\n"
        f"✍️ الخطوة 1/2 — ارسل الإيميل:"
    )

async def admin_reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[3])
    order = get_order(order_id)
    admin_id = update.effective_user.id

    if not order or order[5] != "pending":
        await query.edit_message_text("❌ الطلب مش موجود أو اتعامل معاه قبل كده!")
        return

    update_order_status(order_id, "rejected")
    log_admin_action(admin_id, "reject_order", "order", order_id, "")

    if order[7] == "رصيد":
        update_user_balance(order[1], order[4])

    try:
        refund_text = "💳 تم إرجاع المبلغ لرصيدك.\n" if order[7] == "رصيد" else ""
        await context.bot.send_message(
            chat_id=order[1],
            text=(
                f"❌ تم رفض طلبك!\n\n"
                f"🛍 الطلب رقم: #{order_id}\n"
                f"💰 المبلغ: {order[4]:.0f} ج.م\n\n"
                f"{refund_text}"
                f"📩 تواصل مع الدعم لو عندك استفسار."
            )
        )
    except Exception as e:
        logger.error(f"Failed to notify user {order[1]}: {e}")

    await query.edit_message_text(f"❌ تم رفض الطلب #{order_id}")

async def admin_note_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[3])
    context.user_data["admin_state"] = "order_note"
    context.user_data["note_order_id"] = order_id
    await query.edit_message_text(f"📝 ارسل الملاحظة للطلب #{order_id}:")

async def admin_confirm_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    recharge_id = int(query.data.split("_")[3])
    recharge = get_recharge(recharge_id)
    admin_id = update.effective_user.id

    if not recharge or recharge[4] != "pending":
        await query.edit_message_text("❌ طلب الشحن مش موجود أو اتعامل معاه قبل كده!")
        return

    update_recharge_status(recharge_id, "completed")
    update_user_balance(recharge[1], recharge[2])
    log_admin_action(admin_id, "confirm_recharge", "recharge", recharge_id, f"Amount: {recharge[2]}")

    try:
        await context.bot.send_message(
            chat_id=recharge[1],
            text=(
                f"✅ تم شحن رصيدك!\n\n"
                f"💰 المبلغ: {recharge[2]:.0f} ج.م\n"
                f"📱 تفاصيل التحويل: {html.escape(recharge[3])}\n\n"
                f"🎉 الرصيد ضاف للمحفظة بتاعتك!"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify user {recharge[1]}: {e}")

    await query.edit_message_text(f"✅ تم تأكيد شحن رصيد #{recharge_id}")

async def admin_reject_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    recharge_id = int(query.data.split("_")[3])
    recharge = get_recharge(recharge_id)
    admin_id = update.effective_user.id

    if not recharge or recharge[4] != "pending":
        await query.edit_message_text("❌ طلب الشحن مش موجود أو اتعامل معاه قبل كده!")
        return

    update_recharge_status(recharge_id, "rejected")
    log_admin_action(admin_id, "reject_recharge", "recharge", recharge_id, "")

    try:
        await context.bot.send_message(
            chat_id=recharge[1],
            text=(
                f"❌ تم رفض طلب شحن الرصيد!\n\n"
                f"💰 المبلغ: {recharge[2]:.0f} ج.م\n"
                f"📩 تواصل مع الدعم لو عندك استفسار."
            )
        )
    except Exception as e:
        logger.error(f"Failed to notify user {recharge[1]}: {e}")

    await query.edit_message_text(f"❌ تم رفض شحن رصيد #{recharge_id}")

async def admin_note_recharge_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    recharge_id = int(query.data.split("_")[3])
    context.user_data["admin_state"] = "recharge_note"
    context.user_data["note_recharge_id"] = recharge_id
    await query.edit_message_text(f"📝 ارسل الملاحظة لطلب الشحن #{recharge_id}:")


# ==================== PRODUCT EDIT/REORDER ====================
async def admin_edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[3])
    product = get_product(product_id)
    context.user_data["edit_product_id"] = product_id
    buttons = [
        [InlineKeyboardButton("📝 الاسم", callback_data="admin_edit_field_name")],
        [InlineKeyboardButton("💰 السعر", callback_data="admin_edit_field_price")],
        [InlineKeyboardButton("📦 المخزون", callback_data="admin_edit_field_stock")],
        [InlineKeyboardButton("⏳ الضمان", callback_data="admin_edit_field_warranty")],
        [InlineKeyboardButton("😀 الإيموجي", callback_data="admin_edit_field_emoji")],
        [InlineKeyboardButton("📉 الخصم", callback_data="admin_edit_field_discount")],
        [InlineKeyboardButton("✨ المميزات", callback_data="admin_edit_field_features")],
        [InlineKeyboardButton("🏷️ التصنيف", callback_data="admin_edit_field_category")],
        [InlineKeyboardButton("🔢 يحتاج أكونت", callback_data="admin_edit_field_requires_account")],
        [InlineKeyboardButton("🖼️ صورة المنتج", callback_data="admin_edit_field_image_file_id")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_edit_product")],
    ]
    await query.edit_message_text(
        f"✏️ تعديل: {product[1]}\n\nاختار الحقل:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def admin_edit_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.split("_")[3]
    context.user_data["edit_field"] = field
    context.user_data["admin_state"] = "edit_value"
    field_names = {
        "name": "الاسم", "price": "السعر (رقم)", "stock": "المخزون (رقم)",
        "warranty": "الضمان بالأيام (رقم)", "emoji": "الإيموجي",
        "discount": "نسبة الخصم (رقم)", "features": "المميزات (مفصولة بـ |)",
        "category": "التصنيف", "requires_account": "يحتاج أكونت (0 أو 1)",
        "image_file_id": "صورة المنتج (ارسل صورة جديدة)"
    }
    if field == "image_file_id":
        context.user_data["admin_state"] = "edit_image"
        await query.edit_message_text("🖼️ ارسل صورة المنتج الجديدة:")
    else:
        await query.edit_message_text(f"✏️ تعديل {field_names.get(field, field)}\n\nارسل القيمة الجديدة:")

async def admin_reorder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = get_all_products(active_only=False)
    if not products:
        await query.edit_message_text("❌ مفيش منتجات!")
        return
    buttons = []
    for p in products:
        buttons.append([
            InlineKeyboardButton("⬆️", callback_data=f"admin_reorder_up_{p[0]}"),
            InlineKeyboardButton(f"{p[5]} {p[1]} (ترتيب: {p[9]})", callback_data="noop"),
            InlineKeyboardButton("⬇️", callback_data=f"admin_reorder_down_{p[0]}"),
        ])
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_products_menu")])
    await query.edit_message_text(
        "📋 ترتيب المنتجات\n\nاضغط ⬆️ أو ⬇️:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def admin_reorder_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    product_id = int(parts[3])
    direction = parts[2]
    product = get_product(product_id)
    current_order = product[9]
    new_order = current_order - 1 if direction == "up" else current_order + 1
    if new_order < 1:
        await query.answer("❌ وصلت للأول!")
        return
    reorder_product(product_id, new_order)
    await admin_reorder_start(update, context)


# ==================== USERS ADVANCED HANDLERS ====================
async def admin_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    u = get_user(user_id)
    if not u:
        return "❌ المستخدم مش موجود!"
    orders = get_user_orders(user_id, 5)
    spent = get_user_total_spent(user_id)
    ban_status = "🚫 محظور" if u[7] == 1 else "✅ نشط"
    text = (
        f"👤 تفاصيل المستخدم\n\n"
        f"🆔 ID: {u[0]}\n"
        f"👤 الاسم: {u[2] or u[3] or 'N/A'}\n"
        f"📛 اليوزر: @{u[1] or 'N/A'}\n"
        f"💰 الرصيد: {u[4]:.0f} ج.م\n"
        f"📅 انضم: {u[5]}\n"
        f"🧾 الطلبات: {get_user_orders_count(u[0])}\n"
        f"💵 إجمالي مشتريات: {spent:.0f} ج.م\n"
        f"📊 الحالة: {ban_status}\n"
    )
    if orders:
        text += "\n📦 آخر الطلبات:\n"
        for o in orders:
            status = "✅" if o[6] == "completed" else "⏳" if o[6] == "pending" else "❌"
            text += f"{status} #{o[0]} | {o[12]} | {o[4]:.0f}ج\n"
    return text


# ==================== ENHANCED ADMIN TEXT HANDLER ====================
async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    admin_state = context.user_data.get("admin_state", "")
    temp_product = context.user_data.get("temp_product", {})
    admin_id = update.effective_user.id

    if admin_state == "add_name":
        temp_product["name"] = text
        context.user_data["temp_product"] = temp_product
        context.user_data["admin_state"] = "add_price"
        await update.message.reply_text("➕ إضافة منتج جديد\n\nالخطوة 2/8\n💰 ارسل السعر (رقم فقط):")
    elif admin_state == "add_price":
        try:
            temp_product["price"] = float(text)
            context.user_data["temp_product"] = temp_product
            context.user_data["admin_state"] = "add_stock"
            await update.message.reply_text("➕ الخطوة 3/8\n📦 ارسل الكمية المتاحة:")
        except ValueError:
            await update.message.reply_text("❌ لازم يكون رقم!")
    elif admin_state == "add_stock":
        try:
            temp_product["stock"] = int(text)
            context.user_data["temp_product"] = temp_product
            context.user_data["admin_state"] = "add_emoji"
            await update.message.reply_text("➕ الخطوة 4/8\n😀 ارسل الإيموجي (الشكل) اللي هيظهر جنب اسم المنتج:")
        except ValueError:
            await update.message.reply_text("❌ لازم يكون رقم!")
    elif admin_state == "add_emoji":
        temp_product["emoji"] = text.strip()
        context.user_data["temp_product"] = temp_product
        auto_desc = generate_auto_description(temp_product["name"])
        temp_product["auto_description"] = auto_desc
        context.user_data["temp_product"] = temp_product
        context.user_data["admin_state"] = "confirm_description"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ أوافق على الوصف", callback_data="admin_desc_approve")],
            [InlineKeyboardButton("✏️ اكتب وصف من عندي", callback_data="admin_desc_manual")],
        ])
        await update.message.reply_text(
            f"➕ الخطوة 5/8\n📝 الوصف التلقائي للمنتج:\n\n"
            f"<i>{auto_desc}</i>\n\n"
            f"👇 اختار:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    elif admin_state == "add_description_manual":
        temp_product["features"] = text
        context.user_data["temp_product"] = temp_product
        context.user_data["admin_state"] = "add_image"
        await update.message.reply_text(
            "➕ الخطوة 6/8\n🖼️ ارسل صورة للمنتج (أو اكتب No لو مفيش صورة):"
        )
    elif admin_state == "add_image":
        if text.strip().lower() == "no":
            temp_product["image_file_id"] = ""
        else:
            await update.message.reply_text("❌ ارسل صورة أو اكتب No")
            return
        context.user_data["temp_product"] = temp_product
        context.user_data["admin_state"] = "add_requires_account"
        await update.message.reply_text(
            "➕ الخطوة 7/8\n\n"
            "هل المنتج يحتاج أكونت جاهز من الأدمن؟\n"
            "0 = لا (يتفعل على إيميل العميل الشخصي)\n"
            "1 = نعم (أكونت جاهز من الأدمن)"
        )
    elif admin_state == "add_requires_account":
        try:
            temp_product["requires_account"] = int(text)
            cats = get_all_categories()
            cats_text = "\n".join([f"• {c[1]} ({c[2]})" for c in cats]) if cats else "مفيش فئات"
            context.user_data["temp_product"] = temp_product
            context.user_data["admin_state"] = "add_category"
            await update.message.reply_text(
                f"➕ الخطوة 8/8\n🏷️ اختار/اكتب الفئة:\n{cats_text}"
            )
        except ValueError:
            await update.message.reply_text("❌ لازم 0 أو 1!")
    elif admin_state == "add_category":
        temp_product["category"] = text.strip()
        product_id = add_product(
            temp_product["name"], temp_product["price"], temp_product["stock"],
            temp_product.get("warranty", 30), temp_product["emoji"], temp_product.get("discount", 0),
            temp_product["features"], temp_product["category"], temp_product["requires_account"],
            temp_product.get("image_file_id", "")
        )
        log_admin_action(admin_id, "add_product", "product", product_id, temp_product["name"])
        context.user_data.pop("temp_product", None)
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text(
            f"✅ تم إضافة المنتج!\n\n🛍 {temp_product['name']}\n🆔 ID: {product_id}",
            reply_markup=admin_dashboard_keyboard()
        )

    elif admin_state == "edit_value":
        edit_product_id = context.user_data.get("edit_product_id")
        edit_field = context.user_data.get("edit_field")
        if edit_field in ["price", "stock", "warranty", "discount", "requires_account"]:
            try:
                value = float(text) if edit_field == "price" else int(text)
            except ValueError:
                await update.message.reply_text("❌ لازم يكون رقم!")
                return
        else:
            value = text
        update_product(edit_product_id, edit_field, value)
        log_admin_action(admin_id, f"edit_product_{edit_field}", "product", edit_product_id, str(value))
        context.user_data["admin_state"] = "menu"
        context.user_data.pop("edit_product_id", None)
        context.user_data.pop("edit_field", None)
        await update.message.reply_text("✅ تم التعديل بنجاح!", reply_markup=admin_dashboard_keyboard())

    elif admin_state == "search_user":
        users = search_users(text.strip())
        if not users:
            await update.message.reply_text("❌ مفيش نتائج!", reply_markup=admin_users_menu_keyboard())
        else:
            for u in users[:5]:
                detail = await admin_user_detail(update, context, u[0])
                await update.message.reply_text(detail, reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 تعديل رصيد", callback_data=f"admin_user_balance_{u[0]}")],
                    [InlineKeyboardButton("🚫 حظر/فك حظر", callback_data=f"admin_user_ban_{u[0]}")],
                ]))
        context.user_data["admin_state"] = "menu"

    elif admin_state == "edit_balance_user_id":
        try:
            target_id = int(text.strip())
            context.user_data["edit_balance_target"] = target_id
            context.user_data["admin_state"] = "edit_balance_amount"
            await update.message.reply_text(f"💰 ارسل المبلغ (موجب للإضافة، سالب للخصم) للمستخدم {target_id}:")
        except ValueError:
            await update.message.reply_text("❌ لازم ID رقمي!")
    elif admin_state == "edit_balance_amount":
        try:
            amount = float(text.strip())
            target_id = context.user_data.get("edit_balance_target")
            update_user_balance(target_id, amount)
            log_admin_action(admin_id, "edit_balance", "user", target_id, f"Amount: {amount}")
            context.user_data.pop("edit_balance_target", None)
            context.user_data["admin_state"] = "menu"
            action = "إضافة" if amount > 0 else "خصم"
            await update.message.reply_text(f"✅ تم {action} {abs(amount):.0f} ج.م للمستخدم {target_id}", reply_markup=admin_dashboard_keyboard())
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"📢 تم {action} {abs(amount):.0f} ج.م من رصيدك بواسطة الأدمن."
                )
            except:
                pass
        except ValueError:
            await update.message.reply_text("❌ لازم رقم!")

    elif admin_state == "ban_user_id":
        try:
            target_id = int(text.strip())
            user = get_user(target_id)
            if user:
                new_status = 0 if user[7] == 1 else 1
                ban_user(target_id, new_status)
                status_text = "فك حظر" if new_status == 0 else "حظر"
                await update.message.reply_text(f"✅ تم {status_text} المستخدم {target_id}", reply_markup=admin_dashboard_keyboard())
                try:
                    if new_status == 1:
                        await context.bot.send_message(chat_id=target_id, text="🚫 تم حظرك من استخدام البوت.")
                    else:
                        await context.bot.send_message(chat_id=target_id, text="✅ تم فك حظرك، يمكنك استخدام البوت تاني.")
                except Exception:
                    pass
            else:
                await update.message.reply_text("❌ المستخدم مش موجود!", reply_markup=admin_dashboard_keyboard())
            context.user_data["admin_state"] = "menu"
        except ValueError:
            await update.message.reply_text("❌ لازم ID يكون أرقام بس!", reply_markup=admin_dashboard_keyboard())

    elif admin_state == "coupon_code":
        context.user_data["temp_coupon"]["code"] = text.strip().upper()
        context.user_data["admin_state"] = "coupon_discount"
        await update.message.reply_text("🎟 إنشاء كوبون جديد\n\nالخطوة 2/4\n📉 ارسل نسبة الخصم (رقم %):")
    elif admin_state == "coupon_discount":
        try:
            context.user_data["temp_coupon"]["discount"] = int(text)
            context.user_data["admin_state"] = "coupon_max_uses"
            await update.message.reply_text("🎟 إنشاء كوبون جديد\n\nالخطوة 3/4\n🎯 ارسل عدد الاستخدامات المسموح:")
        except ValueError:
            await update.message.reply_text("❌ لازم رقم!")
    elif admin_state == "coupon_max_uses":
        try:
            context.user_data["temp_coupon"]["max_uses"] = int(text)
            context.user_data["admin_state"] = "coupon_min_order"
            await update.message.reply_text("🎟 إنشاء كوبون جديد\n\nالخطوة 4/4\n🏷️ ارسل الحد الأدنى للطلب (0 = مفيش):")
        except ValueError:
            await update.message.reply_text("❌ لازم رقم!")
    elif admin_state == "coupon_min_order":
        try:
            min_order = float(text)
            tc = context.user_data["temp_coupon"]
            create_coupon(tc["code"], tc["discount"], tc["max_uses"], admin_id, None, min_order)
            log_admin_action(admin_id, "create_coupon", "coupon", tc["code"], f"{tc['discount']}%")
            context.user_data.pop("temp_coupon", None)
            context.user_data["admin_state"] = "menu"
            await update.message.reply_text(f"✅ تم إنشاء الكوبون: {tc['code']}", reply_markup=admin_coupons_menu_keyboard())
        except ValueError:
            await update.message.reply_text("❌ لازم رقم!")

    elif admin_state == "category_name":
        context.user_data["temp_category_name"] = text.strip()
        context.user_data["admin_state"] = "category_emoji"
        await update.message.reply_text("📂 ارسل إيموجي الفئة (مثال: 📱):")
    elif admin_state == "category_emoji":
        name = context.user_data.pop("temp_category_name", "")
        cat_id = add_category(name, text.strip())
        if cat_id:
            log_admin_action(admin_id, "add_category", "category", cat_id, name)
            await update.message.reply_text(f"✅ تم إضافة الفئة: {name}", reply_markup=admin_categories_menu_keyboard())
        else:
            await update.message.reply_text("❌ الفئة موجودة بالفعل!")
        context.user_data["admin_state"] = "menu"

    elif admin_state == "set_wallet":
        set_setting("wallet_number", text.strip())
        log_admin_action(admin_id, "update_setting", "setting", "wallet_number", "")
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text("✅ تم تحديث رقم المحفظة!", reply_markup=admin_settings_menu_keyboard())
    elif admin_state == "set_usdt":
        set_setting("usdt_address", text.strip())
        log_admin_action(admin_id, "update_setting", "setting", "usdt_address", "")
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text("✅ تم تحديث عنوان USDT!", reply_markup=admin_settings_menu_keyboard())
    elif admin_state == "set_support":
        set_setting("support_username", text.strip())
        log_admin_action(admin_id, "update_setting", "setting", "support_username", "")
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text("✅ تم تحديث يوزر الدعم!", reply_markup=admin_settings_menu_keyboard())
    elif admin_state == "set_botname":
        set_setting("bot_name", text.strip())
        log_admin_action(admin_id, "update_setting", "setting", "bot_name", "")
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text("✅ تم تحديث اسم البوت!", reply_markup=admin_settings_menu_keyboard())
    elif admin_state == "set_welcome":
        set_setting("welcome_message", text.strip())
        log_admin_action(admin_id, "update_setting", "setting", "welcome_message", "")
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text("✅ تم تحديث رسالة الترحيب!", reply_markup=admin_settings_menu_keyboard())
    elif admin_state == "set_usd_rate":
        try:
            set_setting("usd_rate", str(float(text)))
            log_admin_action(admin_id, "update_setting", "setting", "usd_rate", text)
            context.user_data["admin_state"] = "menu"
            await update.message.reply_text("✅ تم تحديث سعر الدولار!", reply_markup=admin_settings_menu_keyboard())
        except ValueError:
            await update.message.reply_text("❌ لازم رقم!")

    elif admin_state == "broadcast_all":
        if text.strip() == "/cancel":
            context.user_data["admin_state"] = "menu"
            await update.message.reply_text("❌ تم الإلغاء.", reply_markup=admin_dashboard_keyboard())
            return
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
        users = cursor.fetchall()
        conn.close()
        sent = 0
        failed = 0
        for u in users:
            try:
                await context.bot.send_message(chat_id=u[0], text=text)
                sent += 1
            except:
                failed += 1
        log_admin_action(admin_id, "broadcast", "all", "", f"Sent: {sent}, Failed: {failed}")
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text(f"📢 تم الإرسال!\n✅ نجح: {sent}\n❌ فشل: {failed}", reply_markup=admin_dashboard_keyboard())
    elif admin_state == "broadcast_user_id":
        try:
            target_id = int(text.strip())
            context.user_data["broadcast_target"] = target_id
            context.user_data["admin_state"] = "broadcast_user_msg"
            await update.message.reply_text("👤 ارسل الرسالة اللي عايز تبعتها:")
        except ValueError:
            await update.message.reply_text("❌ لازم ID رقمي!")
    elif admin_state == "broadcast_user_msg":
        target_id = context.user_data.pop("broadcast_target", None)
        try:
            await context.bot.send_message(chat_id=target_id, text=text)
            log_admin_action(admin_id, "broadcast", "user", target_id, "")
            await update.message.reply_text("✅ تم الإرسال!", reply_markup=admin_dashboard_keyboard())
        except Exception as e:
            await update.message.reply_text(f"❌ فشل الإرسال: {e}")
        context.user_data["admin_state"] = "menu"

    elif admin_state == "order_note":
        order_id = context.user_data.pop("note_order_id", None)
        update_order_notes(order_id, text.strip())
        log_admin_action(admin_id, "add_note", "order", order_id, text[:50])
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text(f"✅ تم إضافة الملاحظة للطلب #{order_id}", reply_markup=admin_orders_menu_keyboard())
    elif admin_state == "recharge_note":
        recharge_id = context.user_data.pop("note_recharge_id", None)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE recharges SET admin_notes = ? WHERE id = ?", (text.strip(), recharge_id))
        conn.commit()
        conn.close()
        log_admin_action(admin_id, "add_note", "recharge", recharge_id, text[:50])
        context.user_data["admin_state"] = "menu"
        await update.message.reply_text(f"✅ تم إضافة الملاحظة لطلب الشحن #{recharge_id}", reply_markup=admin_recharges_menu_keyboard())

    elif admin_state == "logs_search":
        conn = get_db()
        cursor = conn.cursor()
        like = f"%{text.strip()}%"
        cursor.execute("SELECT * FROM admin_logs WHERE action LIKE ? OR details LIKE ? OR target_id LIKE ? ORDER BY created_at DESC LIMIT 30",
                       (like, like, like))
        logs = cursor.fetchall()
        conn.close()
        if not logs:
            await update.message.reply_text("❌ مفيش نتائج!")
        else:
            msg = f'🔍 نتائج البحث عن "{text.strip()}":\n\n'
            for log in logs[:20]:
                msg += f"🕐 {log[6]} | {log[2]} | {log[3]}:{log[4]}\n"
            await update.message.reply_text(msg)
        context.user_data["admin_state"] = "menu"


# ==================== PRODUCT & ORDER HANDLERS (USER) ====================
async def products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = context.user_data.get("product_page", 0)
    products, total = get_products(page)
    arabic_months = {
        1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
        5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
        9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
    }
    now = datetime.now()
    date_str = f"{now.day} {arabic_months[now.month]}"
    text = f"📅 {date_str}\n\n🛍 اختار المنتج اللي عايزه:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=products_inline_keyboard(products, page, total))
    else:
        await update.message.reply_text(text, reply_markup=products_inline_keyboard(products, page, total))

async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    product = get_product(product_id)
    if not product:
        await query.edit_message_text("❌ المنتج مش موجود!")
        return
    features = product[7].split("|") if product[7] else []
    features_text = "\n".join([f"• {f}" for f in features])
    discount_text = f"📉 خصم: {product[6]}%\n" if product[6] > 0 else ""
    final_price = product[2] * (1 - product[6] / 100)
    price_text = f"💰 السعر: {final_price:.0f} ج.م" if product[6] > 0 else f"💰 السعر: {product[2]:.0f} ج.م"
    old_price = f"~~{product[2]:.0f}~~ " if product[6] > 0 else ""
    image_file_id = product[13] if len(product) > 13 else ""

    text = (
        f"🛍 {product[1]}\n\n"
        f"{old_price}{price_text}\n"
        f"{discount_text}"
        f"📦 المتوفر: {product[3]}\n"
        f"⏳ الضمان: {product[4]} يوم\n"
        f"🏷️ الفئة: {product[8]}\n\n"
        f"✨ مميزات {product[1]}:\n"
        f"{features_text}\n\n"
        f"🚀 التسليم تلقائي فوري بعد تأكيد الدفع"
    )

    if image_file_id:
        try:
            await query.delete_message()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_file_id,
                caption=text,
                reply_markup=product_detail_keyboard(product_id)
            )
            return
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")

    await query.edit_message_text(text, reply_markup=product_detail_keyboard(product_id))

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    product = get_product(product_id)
    if not product or product[3] <= 0:
        await query.answer("❌ المنتج نفذ من المخزون!", show_alert=True)
        return
    context.user_data["selected_product"] = product_id
    text = (
        f"🛒 اختر الكمية\n"
        f"🛍 {product[1]}\n"
        f"💰 سعر الوحدة: {product[2]:.0f} ج.م\n"
        f"📦 المتوفر: {product[3]}\n\n"
        f"👇 هتشتري كام؟"
    )
    await query.edit_message_text(text, reply_markup=quantity_keyboard(product_id, product[3]))

async def select_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    product_id = int(parts[1])
    quantity = int(parts[2])
    product = get_product(product_id)
    user = update.effective_user
    user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    balance = user_data[4] if user_data[4] else 0
    unit_price = product[2]
    total_price = unit_price * quantity
    usd_rate = float(get_setting("usd_rate", "50"))
    usd_price = total_price / usd_rate
    requires_account = product[10] if len(product) > 10 else 0
    context.user_data["order"] = {
        "product_id": product_id, "quantity": quantity,
        "total_price": total_price, "unit_price": unit_price, "discount_amount": 0,
    }
    if requires_account == 0:
        context.user_data["awaiting_client_email"] = True
        await query.edit_message_text(
            f"📧 الخدمة دي بتتفعل على أكونتك الشخصي.\n\n"
            f"🛍 {product[1]}\n"
            f"🔢 الكمية: {quantity}\n"
            f"🧮 الإجمالي: {total_price:.0f} ج.م\n\n"
            f"✍️ ارسل الإيميل/الإيميلات اللي هيتفعل عليها (إيميل في كل سطر):"
        )
        return
    text = (
        f"🧾 ملخص الطلب\n"
        f"🛍 {product[1]}\n"
        f"🔢 الكمية: {quantity}\n"
        f"💰 سعر الوحدة: {unit_price:.0f} ج.م\n"
        f"🧮 الإجمالي: {total_price:.0f} ج.م\n"
        f"💵 يعادل بالدولار: ${usd_price:.2f}\n"
        f"💳 رصيدك: {balance:.0f} ج.م\n\n"
        f"👇 اختار طريقة الدفع"
    )
    await query.edit_message_text(text, reply_markup=payment_methods_keyboard())

async def pay_from_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    balance = user_data[4] if user_data[4] else 0
    order_data = context.user_data.get("order")
    if not order_data:
        await query.answer("❌ مفيش طلب نشط!", show_alert=True)
        return
    total_price = order_data["total_price"]
    if balance < total_price:
        remaining = total_price - balance
        await query.answer()
        text = (
            f"⚠️ رصيدك غير كافي!\n\n"
            f"💰 المطلوب: {total_price:.0f} ج.م\n"
            f"💳 رصيدك: {balance:.0f} ج.م\n"
            f"📉 النقص: {remaining:.0f} ج.م\n\n"
            f"👇 لتعبئة محفظتك 'شحن رصيد' اضغط على"
        )
        await query.edit_message_text(text, reply_markup=wallet_inline_keyboard())
        return
    await query.answer()
    product = get_product(order_data["product_id"])
    requires_account = product[10] if len(product) > 10 else 0
    client_email = context.user_data.get("client_email", "")
    coupon_code = context.user_data.get("applied_coupon", "")
    discount_amount = context.user_data.get("coupon_discount", 0)
    update_user_balance(user.id, -total_price)
    if requires_account == 1:
        order_id = create_order(user.id, order_data["product_id"], order_data["quantity"], total_price, "رصيد", "", "", "", "", coupon_code, discount_amount)
    else:
        order_id = create_order(user.id, order_data["product_id"], order_data["quantity"], total_price, "رصيد", client_email, "", "", "", coupon_code, discount_amount)
    await query.edit_message_text(
        "⏳ تم إرسال طلبك للأدمن!\n\n"
        f"🛍 {product[1]}\n"
        f"🔢 الكمية: {order_data['quantity']}\n"
        f"🧮 الإجمالي: {total_price:.0f} ج.م\n"
        f"💳 تم خصم المبلغ من رصيدك\n\n"
        "✅ هنرد عليك في خلال دقايق!"
    )
    await notify_admins_order(context, order_id, user, product, order_data["quantity"], total_price, "رصيد", client_email)
    context.user_data.pop("order", None)
    context.user_data.pop("client_email", None)
    context.user_data.pop("applied_coupon", None)
    context.user_data.pop("coupon_discount", None)

async def binance_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_data = context.user_data.get("order")
    if not order_data:
        await query.edit_message_text("❌ مفيش طلب نشط!")
        return
    total_price = order_data["total_price"]
    usd_rate = float(get_setting("usd_rate", "50"))
    usd_price = total_price / usd_rate
    usdt_addr = get_setting("usdt_address", "YOUR_USDT_TRC20_ADDRESS_HERE")
    text = (
        f"✅ تمام. ادفع ${usd_price:.2f} USDT على شبكة USDT:\n\n"
        f"🅱️ 1267938246\n"
        f"<code>{usdt_addr}</code>\n\n"
        f"⚠️ لازم تبعت نفس المبلغ بالظبط\n"
        f"⚠️ شبكة USDT بس — لو حوّلت على شبكة تانية فلوسك هتضيع\n\n"
        f"وبعد التحويل، ابعت Order ID هنا للمراجعة 👇"
    )
    await query.edit_message_text(text, parse_mode="HTML")
    context.user_data["awaiting_payment_confirmation"] = True
    context.user_data["payment_type"] = "order"
    context.user_data["order_payment_method"] = "بينانس USDT (يدوي)"


# ==================== COUPON SYSTEM ====================
async def apply_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_data = context.user_data.get("order")
    if not order_data:
        await query.edit_message_text("❌ مفيش طلب نشط!")
        return
    context.user_data["awaiting_coupon"] = True
    await query.edit_message_text("🎟 ارسل كود الكوبون:")

async def process_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE, coupon_code):
    order_data = context.user_data.get("order")
    if not order_data:
        await update.message.reply_text("❌ مفيش طلب نشط!")
        return
    coupon = get_coupon(coupon_code)
    if not coupon:
        await update.message.reply_text("❌ الكوبون غير صحيح أو منتهي!")
        return
    if coupon[3] >= coupon[2]:
        await update.message.reply_text("❌ الكوبون استنفذ عدد الاستخدامات!")
        return
    if coupon[5] and coupon[5] < datetime.now().strftime("%Y-%m-%d"):
        await update.message.reply_text("❌ الكوبون منتهي الصلاحية!")
        return
    if order_data["total_price"] < coupon[7]:
        await update.message.reply_text(f"❌ الحد الأدنى للطلب: {coupon[7]:.0f} ج.م")
        return
    discount = order_data["total_price"] * (coupon[1] / 100)
    new_total = order_data["total_price"] - discount
    order_data["total_price"] = new_total
    order_data["discount_amount"] = discount
    context.user_data["order"] = order_data
    context.user_data["applied_coupon"] = coupon_code
    context.user_data["coupon_discount"] = discount
    use_coupon(coupon_code)
    product = get_product(order_data["product_id"])
    user = update.effective_user
    user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    balance = user_data[4] if user_data[4] else 0
    usd_rate = float(get_setting("usd_rate", "50"))
    usd_price = new_total / usd_rate
    text = (
        f"🎟 تم تطبيق الكوبون!\n"
        f"📉 خصم: {discount:.0f} ج.م ({coupon[1]}%)\n\n"
        f"🧾 ملخص الطلب\n"
        f"🛍 {product[1]}\n"
        f"🔢 الكمية: {order_data['quantity']}\n"
        f"💰 الإجمالي الجديد: {new_total:.0f} ج.م\n"
        f"💵 يعادل بالدولار: ${usd_price:.2f}\n"
        f"💳 رصيدك: {balance:.0f} ج.م\n\n"
        f"👇 اختار طريقة الدفع"
    )
    await update.message.reply_text(text, reply_markup=payment_methods_keyboard())


# ==================== COUPONS HANDLER (MAIN MENU) ====================
async def coupons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coupons = get_all_coupons()
    now = datetime.now().strftime("%Y-%m-%d")
    active_coupons = []
    for c in coupons:
        if c[6] == 1 and (not c[5] or c[5] >= now) and c[3] < c[2]:
            active_coupons.append(c)

    if not active_coupons:
        text = "🎟 مفيش كوبونات متاحة حالياً!\n\nتابعنا عشان تعرف الكوبونات الجديدة أول بأول."
    else:
        text = "🎟 الكوبونات المتاحة:\n\n"
        for c in active_coupons:
            text += f"• <code>{c[0]}</code> — خصم {c[1]}% (حد أدنى {c[7]:.0f}ج)\n"
        text += "\n✨ اضغط على المنتجات واستخدم الكوبون أثناء الدفع!"

    await update.message.reply_text(text, reply_markup=main_menu_keyboard(update.effective_user.id), parse_mode="HTML")


# ==================== PHOTO HANDLER (ADMIN) ====================
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not (is_admin(user.id) or is_admin_session_active(user.id)):
        return

    admin_state = context.user_data.get("admin_state", "")
    if admin_state == "add_image":
        photo = update.message.photo[-1]
        file_id = photo.file_id
        temp_product = context.user_data.get("temp_product", {})
        temp_product["image_file_id"] = file_id
        context.user_data["temp_product"] = temp_product
        context.user_data["admin_state"] = "add_requires_account"
        await update.message.reply_text(
            "➕ الخطوة 7/8\n✅ تم حفظ الصورة\n\n"
            "هل المنتج يحتاج أكونت جاهز من الأدمن؟\n"
            "0 = لا (يتفعل على إيميل العميل الشخصي)\n"
            "1 = نعم (أكونت جاهز من الأدمن)"
        )
    elif admin_state == "edit_image":
        photo = update.message.photo[-1]
        file_id = photo.file_id
        edit_product_id = context.user_data.get("edit_product_id")
        update_product(edit_product_id, "image_file_id", file_id)
        log_admin_action(user.id, "edit_product_image", "product", edit_product_id, "")
        context.user_data["admin_state"] = "menu"
        context.user_data.pop("edit_product_id", None)
        context.user_data.pop("edit_field", None)
        await update.message.reply_text("✅ تم تحديث صورة المنتج!", reply_markup=admin_dashboard_keyboard())
    else:
        await update.message.reply_text("🤔 مفيش طلب صورة حالياً.")


# ==================== FAWATERK GATEWAY ====================
async def initiate_fawaterk_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, method_name: str):
    query = update.callback_query
    await query.answer()
    order_data = context.user_data.get("order")
    if not order_data:
        await query.edit_message_text("❌ مفيش طلب نشط!")
        return
    try:
        token = await get_fawaterk_token()
        product = get_product(order_data["product_id"])
        total_price = order_data["total_price"]
        invoice_data = await create_fawaterk_invoice(token, total_price, product[1], update.effective_user)
        res_data = invoice_data.get("data", {})
        invoice_id = res_data.get("intent_key") or res_data.get("invoice_id") or res_data.get("invoiceId")
        payment_url = res_data.get("url") or res_data.get("payment_url") or res_data.get("redirectTo")
        if not invoice_id or not payment_url:
            await query.edit_message_text("❌ حصل خطأ في استخراج بيانات الفاتورة.")
            return
        client_email = context.user_data.get("client_email", "")
        requires_account = product[10] if len(product) > 10 else 0
        coupon_code = context.user_data.get("applied_coupon", "")
        discount_amount = context.user_data.get("coupon_discount", 0)
        if requires_account == 1:
            order_id = create_order(update.effective_user.id, order_data["product_id"], order_data["quantity"], total_price, f"{method_name} (آلي)", "", "", "", str(invoice_id), coupon_code, discount_amount)
        else:
            order_id = create_order(update.effective_user.id, order_data["product_id"], order_data["quantity"], total_price, f"{method_name} (آلي)", client_email, "", "", str(invoice_id), coupon_code, discount_amount)
        text = (
            f"⚡ تم إنشاء فاتورة الدفع الآلي عبر {method_name}!\n\n"
            f"🛍 {product[1]}\n"
            f"🧮 الإجمالي: {total_price:.0f} ج.م\n\n"
            f"👇 ادفع من الرابط الآمن:\n"
            f"{payment_url}\n\n"
            f"بعد إتمام الدفع، اضغط على زر التحقق:"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تحقق من الدفع", callback_data=f"check_fawaterk_order_{invoice_id}")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]
        ])
        await query.edit_message_text(text, reply_markup=kb, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Fawaterk error: {e}")
        await query.edit_message_text("❌ حصل خطأ في الاتصال ببوابة الدفع.")

async def check_fawaterk_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    invoice_id = query.data.split("_")[3]
    try:
        token = await get_fawaterk_token()
        invoice_data = await check_fawaterk_invoice(token, invoice_id)
        status = invoice_data.get("data", {}).get("invoice_status", "").lower()
        if status == "paid":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE fawaterk_invoice_id = ?", (invoice_id,))
            order = cursor.fetchone()
            conn.close()
            if not order or order[5] == "completed":
                await query.edit_message_text("✅ الطلب اتعامل معاه قبل كده!")
                return
            order_id = order[0]
            product = get_product(order[2])
            requires_account = product[10] if len(product) > 10 else 0
            update_order_status(order_id, "completed")
            update_product_stock(order[2], order[3])
            increment_product_sales(order[2], order[3])
            if requires_account == 1:
                await notify_admins_order(context, order_id, update.effective_user, product, order[3], order[4], f"{order[7]} (بانتظار تسليم الحساب)", order[8])
                await query.edit_message_text("✅ تم تأكيد الدفع!\n\n⏳ الأدمن هيسلملك الحساب.")
            else:
                client_email = order[8] if len(order) > 8 else ""
                msg = f"✅ تم تأكيد الدفع وتفعيل الخدمة!\n\n🛍 الطلب رقم: #{order_id}\n💰 المبلغ: {order[4]:.0f} ج.م\n"
                if client_email:
                    msg += f"📧 تم التفعيل على: <code>{html.escape(client_email)}</code>\n"
                msg += "\n🎉 استمتع بالخدمة!"
                await context.bot.send_message(chat_id=order[1], text=msg, parse_mode="HTML")
                await query.edit_message_text(f"✅ تم تأكيد الدفع وتفعيل طلبك!\n\n🛍 {product[1]}")
        else:
            await query.answer("❌ لم يتم تأكيد الدفع بعد!", show_alert=True)
    except Exception as e:
        logger.error(f"Fawaterk check error: {e}")
        await query.answer("❌ حصل خطأ في التحقق.", show_alert=True)


# ==================== RECHARGE HANDLERS ====================
async def recharge_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💳 اختار طريقة شحن الرصيد:", reply_markup=wallet_inline_keyboard())

async def recharge_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 اختار طريقة شحن الرصيد:", reply_markup=wallet_inline_keyboard())

# ==================== USER ACCOUNT HANDLERS ====================
async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تم استبداله بواجهة المحفظة الجديدة"""
    await wallet_handler(update, context)

async def orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = get_user_orders(user.id)
    if not orders:
        text = "🛒 ماعندكش طلبات لسه!\n\nروح للمنتجات واشتري 🛍"
    else:
        text = "🛒 طلباتك:\n\n"
        for o in orders:
            status_emoji = "✅" if o[6] == "completed" else "⏳" if o[6] == "pending" else "❌"
            text += f"{status_emoji} #{o[0]} | {o[12]} | {o[3]} قطعة | {o[4]:.0f} ج.م | {o[7]}\n"

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=main_inline_menu_keyboard(user.id))
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(user.id))

async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_user = get_setting("support_username", "@SupportUsername")
    text = (
        f"💬 الدعم الفني\n\n"
        f"عندك مشكلة؟ محتاج مساعدة؟\n"
        f"تواصل معانا مباشرة:\n"
        f"{support_user}\n\n"
        f"⏰ مواعيد الرد: من 10 ص لـ 12 ص"
    )
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=main_inline_menu_keyboard(update.effective_user.id))
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(update.effective_user.id))

async def tutorial_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📖 شرح استخدام البوت\n\n"
        '1️⃣ اضغط "المنتجات 🛍" عشان تشوف كل اللي عندنا\n'
        "2️⃣ اختار المنتج اللي عايزه\n"
        '3️⃣ اضغط "شراء الآن" واختار الكمية\n'
        "4️⃣ اختار طريقة الدفع (رصيدك، أو دفع مباشر)\n"
        "5️⃣ بعد الدفع، المنتج هيوصلك فوري! 🚀\n\n"
        '💡 تقدر تشحن رصيدك من "شحن رصيد 💳"\n'
        '💡 تقدر تشوف طلباتك من "طلباتي 🛒"\n\n'
        "سهل صح؟ 😎"
    )
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=main_inline_menu_keyboard(update.effective_user.id))
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(update.effective_user.id))


# ==================== CALLBACK HANDLER ====================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = update.effective_user

    if data.startswith("admin_"):
        if not is_admin(user.id) and not is_admin_session_active(user.id):
            await query.answer("❌ ممنوع!", show_alert=True)
            return

        if data == "admin_add_product":
            await admin_add_product_start(update, context)
        elif data == "admin_list_products":
            await admin_list_products(update, context)
        elif data == "admin_edit_product":
            await admin_edit_product_start(update, context)
        elif data == "admin_delete_product":
            await admin_delete_product_start(update, context)
        elif data == "admin_top_products":
            await admin_top_products(update, context)
        elif data == "admin_products_menu":
            await admin_products_menu(update, context)
        elif data == "admin_orders_menu":
            await admin_orders_menu(update, context)
        elif data == "admin_recharges_menu":
            await admin_recharges_menu(update, context)
        elif data == "admin_coupons_menu":
            await admin_coupons_menu(update, context)
        elif data == "admin_categories_menu":
            await admin_categories_menu(update, context)
        elif data == "admin_settings_menu":
            await admin_settings_menu(update, context)
        elif data == "admin_broadcast_menu":
            await admin_broadcast_menu(update, context)
        elif data == "admin_logs_menu":
            await admin_logs_menu(update, context)
        elif data == "admin_stats_advanced":
            await admin_stats_advanced(update, context)
        elif data == "admin_backup":
            await admin_backup(update, context)
        elif data == "admin_exit":
            context.user_data.clear()
            await exit_admin(update, context)
        elif data == "admin_back":
            await admin_back_to_dashboard(update, context)
        elif data == "admin_desc_approve":
            await query.answer()
            temp_product = context.user_data.get("temp_product", {})
            temp_product["features"] = temp_product.get("auto_description", "")
            context.user_data["temp_product"] = temp_product
            context.user_data["admin_state"] = "add_image"
            await query.edit_message_text(
                "➕ الخطوة 6/8\n🖼️ ارسل صورة للمنتج (أو اكتب No لو مفيش صورة):"
            )
        elif data == "admin_desc_manual":
            await query.answer()
            context.user_data["admin_state"] = "add_description_manual"
            await query.edit_message_text(
                "➕ الخطوة 5/8 (يدوي)\n✏️ ارسل الوصف/المميزات اللي عايزها (مفصولة بـ |):"
            )
        elif data == "admin_users_menu":
            await admin_users_menu(update, context)
        elif data == "admin_list_users":
            await admin_list_users(update, context)
        elif data == "admin_search_user":
            await admin_search_user_start(update, context)
        elif data == "admin_edit_balance":
            await admin_edit_balance_start(update, context)
        elif data == "admin_ban_user":
            await admin_ban_user_start(update, context)
        elif data == "admin_users_stats":
            await admin_users_stats(update, context)
        elif data == "admin_pending_orders":
            await admin_pending_orders(update, context)
        elif data == "admin_completed_orders":
            await admin_completed_orders(update, context)
        elif data == "admin_rejected_orders":
            await admin_rejected_orders(update, context)
        elif data == "admin_search_order":
            await admin_search_order_start(update, context)
        elif data == "admin_orders_stats":
            await admin_orders_stats(update, context)
        elif data == "admin_pending_recharges":
            await admin_pending_recharges(update, context)
        elif data == "admin_completed_recharges":
            await admin_completed_recharges(update, context)
        elif data == "admin_rejected_recharges":
            await admin_rejected_recharges(update, context)
        elif data == "admin_recharges_stats":
            await admin_recharges_stats(update, context)
        elif data == "admin_add_coupon":
            await admin_add_coupon_start(update, context)
        elif data == "admin_list_coupons":
            await admin_list_coupons(update, context)
        elif data == "admin_delete_coupon":
            await admin_delete_coupon_start(update, context)
        elif data == "admin_add_category":
            await admin_add_category_start(update, context)
        elif data == "admin_set_wallet":
            await admin_set_wallet_start(update, context)
        elif data == "admin_set_usdt":
            await admin_set_usdt_start(update, context)
        elif data == "admin_set_support":
            await admin_set_support_start(update, context)
        elif data == "admin_set_botname":
            await admin_set_botname_start(update, context)
        elif data == "admin_set_welcome":
            await admin_set_welcome_start(update, context)
        elif data == "admin_maintenance":
            await admin_maintenance_toggle(update, context)
        elif data == "admin_set_usd_rate":
            await admin_set_usd_rate_start(update, context)
        elif data == "admin_broadcast_all":
            await admin_broadcast_all_start(update, context)
        elif data == "admin_broadcast_user":
            await admin_broadcast_user_start(update, context)
        elif data == "admin_logs_20":
            await admin_logs_show(update, context)
        elif data == "admin_logs_50":
            await admin_logs_show(update, context)
        elif data == "admin_logs_search":
            await admin_logs_search_start(update, context)
        elif data.startswith("admin_edit_select_"):
            await admin_edit_select(update, context)
        elif data.startswith("admin_edit_field_"):
            await admin_edit_field_select(update, context)
        elif data.startswith("admin_toggle_product_"):
            await admin_toggle_product(update, context)
        elif data.startswith("admin_del_coupon_"):
            await admin_delete_coupon_confirm(update, context)
        elif data.startswith("admin_reorder_up_") or data.startswith("admin_reorder_down_"):
            await admin_reorder_move(update, context)
        elif data.startswith("admin_confirm_order_"):
            await admin_confirm_order(update, context)
        elif data.startswith("admin_reject_order_"):
            await admin_reject_order(update, context)
        elif data.startswith("admin_deliver_"):
            await admin_deliver_account(update, context)
        elif data.startswith("admin_note_order_"):
            await admin_note_order_start(update, context)
        elif data.startswith("admin_confirm_recharge_"):
            await admin_confirm_recharge(update, context)
        elif data.startswith("admin_reject_recharge_"):
            await admin_reject_recharge(update, context)
        elif data.startswith("admin_note_recharge_"):
            await admin_note_recharge_start(update, context)
        elif data.startswith("admin_users_page_"):
            context.user_data["users_page"] = int(data.split("_")[3])
            await admin_list_users(update, context)
        elif data.startswith("admin_completed_page_"):
            context.user_data["completed_orders_page"] = int(data.split("_")[3])
            await admin_completed_orders(update, context)
        elif data.startswith("admin_rejected_page_"):
            context.user_data["rejected_orders_page"] = int(data.split("_")[3])
            await admin_rejected_orders(update, context)
        elif data.startswith("admin_rech_comp_page_"):
            context.user_data["completed_recharges_page"] = int(data.split("_")[4])
            await admin_completed_recharges(update, context)
        elif data.startswith("admin_rech_rej_page_"):
            context.user_data["rejected_recharges_page"] = int(data.split("_")[4])
            await admin_rejected_recharges(update, context)
        elif data.startswith("admin_user_balance_"):
            target = int(data.split("_")[3])
            context.user_data["edit_balance_target"] = target
            context.user_data["admin_state"] = "edit_balance_amount"
            await query.edit_message_text(f"💰 ارسل المبلغ للمستخدم {target}:")
        elif data.startswith("admin_user_ban_"):
            target = int(data.split("_")[3])
            u = get_user(target)
            if u:
                new_ban = 0 if u[7] == 1 else 1
                ban_user(target, new_ban)
                status = "حظر" if new_ban else "فك حظر"
                await query.edit_message_text(f"✅ تم {status} المستخدم {target}")
        return

    # القائمة الرئيسية التفاعلية
    if data == "main_menu":
        await query.answer()
        for key in ["awaiting_client_email", "awaiting_custom_qty", "awaiting_coupon",
                    "awaiting_payment_confirmation", "recharge_flow", "recharge_step",
                    "recharge_amount", "recharge_method", "admin_delivering_order",
                    "admin_delivery_order_id", "admin_delivery_step", "admin_delivery_email",
                    "order", "client_email", "applied_coupon", "coupon_discount",
                    "payment_type", "order_payment_method"]:
            context.user_data.pop(key, None)
        await main_menu_handler(update, context)
    elif data == "browse_products":
        await query.answer()
        for key in ["awaiting_client_email", "awaiting_custom_qty", "awaiting_coupon",
                    "awaiting_payment_confirmation", "order", "client_email",
                    "applied_coupon", "coupon_discount"]:
            context.user_data.pop(key, None)
        await products_handler(update, context)
    elif data == "my_orders":
        await query.answer()
        for key in ["awaiting_client_email", "order", "client_email"]:
            context.user_data.pop(key, None)
        await orders_handler(update, context)
    elif data == "my_wallet":
        await query.answer()
        for key in ["awaiting_client_email", "order", "client_email"]:
            context.user_data.pop(key, None)
        await wallet_handler(update, context)
    elif data == "recharge_balance":
        await query.answer()
        for key in ["awaiting_client_email", "order", "client_email"]:
            context.user_data.pop(key, None)
        await recharge_balance(update, context)
    elif data == "my_coupons":
        await query.answer()
        for key in ["awaiting_client_email", "order", "client_email"]:
            context.user_data.pop(key, None)
        await coupons_handler(update, context)
    elif data == "support":
        await query.answer()
        for key in ["awaiting_client_email", "order", "client_email"]:
            context.user_data.pop(key, None)
        await support_handler(update, context)
    elif data == "tutorial":
        await query.answer()
        for key in ["awaiting_client_email", "order", "client_email"]:
            context.user_data.pop(key, None)
        await tutorial_handler(update, context)
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        context.user_data["product_page"] = page
        await products_handler(update, context)
    elif data == "back_to_products":
        await query.answer()
        for key in ["awaiting_client_email", "order", "client_email"]:
            context.user_data.pop(key, None)
        await products_handler(update, context)
    elif data == "back_to_summary":
        await query.answer()
        context.user_data.pop("awaiting_client_email", None)
        order_data = context.user_data.get("order")
        if order_data:
            product = get_product(order_data["product_id"])
            user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
            balance = user_data[4] if user_data[4] else 0
            total_price = order_data["total_price"]
            usd_rate = float(get_setting("usd_rate", "50"))
            usd_price = total_price / usd_rate
            text = (
                f"🧾 ملخص الطلب\n"
                f"🛍 {product[1]}\n"
                f"🔢 الكمية: {order_data['quantity']}\n"
                f"💰 سعر الوحدة: {order_data['unit_price']:.0f} ج.م\n"
                f"🧮 الإجمالي: {total_price:.0f} ج.م\n"
                f"💵 يعادل بالدولار: ${usd_price:.2f}\n"
                f"💳 رصيدك: {balance:.0f} ج.م\n\n"
                f"👇 اختار طريقة الدفع"
            )
            await query.edit_message_text(text, reply_markup=payment_methods_keyboard())
    elif data == "pay_wallet":
        await pay_from_wallet(update, context)
    elif data == "pay_vodafone":
        await initiate_fawaterk_payment(update, context, "فودافون كاش")
    elif data == "pay_instapay":
        await initiate_fawaterk_payment(update, context, "انستا باي")
    elif data == "pay_binance":
        await binance_payment(update, context)
    elif data == "apply_coupon":
        await apply_coupon(update, context)
    elif data == "recharge":
        await recharge_balance(update, context)
    elif data == "recharge_manual_wallet":
        await query.answer()
        context.user_data["recharge_flow"] = True
        context.user_data["recharge_step"] = "amount"
        context.user_data["recharge_method"] = "wallet"
        wallet = get_setting("wallet_number", WALLET_NUMBER)
        wallet_name = get_setting("wallet_name", WALLET_NAME)
        await query.edit_message_text(
            f"📱 شحن رصيد — محفظة إلكترونية\n\n"
            f"💳 المحفظة: <code>{wallet}</code> — {wallet_name}\n"
            f"💰 اكتب المبلغ اللي عايز تحوله (بالجنيه):\n"
            f"*(للإلغاء أرسل /start)*",
            parse_mode="HTML"
        )
    elif data == "recharge_binance":
        await query.answer()
        context.user_data["recharge_flow"] = True
        context.user_data["recharge_step"] = "amount"
        context.user_data["recharge_method"] = "binance"
        await query.edit_message_text(
            "💳 شحن رصيد — بينانس (USDT)\n\n"
            "💰 ارسل المبلغ بالجنيه (رقم فقط):\n"
            "*(للإلغاء أرسل /start)*"
        )
    elif data.startswith("check_fawaterk_order_"):
        await check_fawaterk_order(update, context)
    elif data.startswith("product_"):
        await product_detail(update, context)
    elif data.startswith("buy_"):
        await buy_product(update, context)
    elif data.startswith("qty_"):
        await select_quantity(update, context)
    elif data.startswith("custom_qty_"):
        await query.answer("✍️ ارسل الكمية اللي عايزها (رقم فقط):")
        context.user_data["awaiting_custom_qty"] = int(data.split("_")[2])
    elif data == "noop":
        await query.answer()


# ==================== TEXT HANDLER ====================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    admin_state = context.user_data.get("admin_state", "")

    # Handle admin text inputs FIRST (before clearing states)
    if context.user_data.get("admin_mode") and (is_admin(user.id) or is_admin_session_active(user.id)):
        if admin_state:
            await admin_text_handler(update, context)
            return

    # Handle user flows FIRST
    if context.user_data.get("awaiting_client_email"):
        context.user_data["client_email"] = text.strip()
        context.user_data.pop("awaiting_client_email", None)
        order_data = context.user_data.get("order")
        if order_data:
            product = get_product(order_data["product_id"])
            user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
            balance = user_data[4] if user_data[4] else 0
            total_price = order_data["total_price"]
            usd_rate = float(get_setting("usd_rate", "50"))
            usd_price = total_price / usd_rate
            msg = (
                f"🧾 ملخص الطلب\n"
                f"🛍 {product[1]}\n"
                f"🔢 الكمية: {order_data['quantity']}\n"
                f"💰 سعر الوحدة: {order_data['unit_price']:.0f} ج.م\n"
                f"🧮 الإجمالي: {total_price:.0f} ج.م\n"
                f"💵 يعادل بالدولار: ${usd_price:.2f}\n"
                f"📧 الإيميل: {text.strip()}\n"
                f"💳 رصيدك: {balance:.0f} ج.م\n\n"
                f"👇 اختار طريقة الدفع"
            )
            await update.message.reply_text(msg, reply_markup=payment_methods_keyboard())
        return

    if context.user_data.get("awaiting_custom_qty"):
        try:
            qty = int(text.strip())
            product_id = context.user_data.pop("awaiting_custom_qty")
            product = get_product(product_id)
            if qty > product[3] or qty < 1:
                await update.message.reply_text("❌ الكمية غير متاحة!")
                return
            user_data = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
            balance = user_data[4] if user_data[4] else 0
            unit_price = product[2]
            total_price = unit_price * qty
            usd_rate = float(get_setting("usd_rate", "50"))
            usd_price = total_price / usd_rate
            context.user_data["order"] = {
                "product_id": product_id, "quantity": qty,
                "total_price": total_price, "unit_price": unit_price, "discount_amount": 0,
            }
            requires_account = product[10] if len(product) > 10 else 0
            if requires_account == 0:
                context.user_data["awaiting_client_email"] = True
                await update.message.reply_text(
                    f"📧 الخدمة دي بتتفعل على أكونتك الشخصي.\n\n"
                    f"🛍 {product[1]}\n"
                    f"🔢 الكمية: {qty}\n"
                    f"🧮 الإجمالي: {total_price:.0f} ج.م\n\n"
                    f"✍️ ارسل الإيميل/الإيميلات اللي هيتفعل عليها (إيميل في كل سطر):"
                )
            else:
                msg = (
                    f"🧾 ملخص الطلب\n"
                    f"🛍 {product[1]}\n"
                    f"🔢 الكمية: {qty}\n"
                    f"💰 سعر الوحدة: {unit_price:.0f} ج.م\n"
                    f"🧮 الإجمالي: {total_price:.0f} ج.م\n"
                    f"💵 يعادل بالدولار: ${usd_price:.2f}\n"
                    f"💳 رصيدك: {balance:.0f} ج.م\n\n"
                    f"👇 اختار طريقة الدفع"
                )
                await update.message.reply_text(msg, reply_markup=payment_methods_keyboard())
        except ValueError:
            await update.message.reply_text("❌ لازم رقم!")
        return

    if context.user_data.get("awaiting_coupon"):
        context.user_data.pop("awaiting_coupon", None)
        await process_coupon(update, context, text.strip())
        return

    if context.user_data.get("awaiting_payment_confirmation"):
        context.user_data.pop("awaiting_payment_confirmation", None)
        context.user_data.pop("payment_type", None)
        context.user_data.pop("order_payment_method", None)
        await update.message.reply_text(
            "✅ تم استلام التأكيد! الأدمن هيراجع التحويل ويوافق عليه قريباً.\n"
            "⏳ هنرد عليك في خلال دقايق."
        )
        return

    if context.user_data.get("recharge_flow"):
        step = context.user_data.get("recharge_step")
        if step == "amount":
            try:
                amount = float(text.strip())
                min_recharge = float(get_setting("min_recharge", "5"))
                if amount < min_recharge:
                    await update.message.reply_text(f"❌ الحد الأدنى للشحن: {min_recharge:.0f} ج.م")
                    return
                context.user_data["recharge_amount"] = amount
                context.user_data["recharge_step"] = "phone"
                method = context.user_data.get("recharge_method", "wallet")
                if method == "wallet":
                    wallet = get_setting("wallet_number", WALLET_NUMBER)
                    wallet_name = get_setting("wallet_name", WALLET_NAME)
                    await update.message.reply_text(
                        f"💰 المبلغ: {amount:.0f} ج.م\n\n"
                        f"📱 ارسل رقم المحفظة اللي حوّلت منها:\n"
                        f"*(أو اسمك + رقم التحويل)*"
                    )
                else:
                    usd_rate = float(get_setting("usd_rate", "50"))
                    usd_amount = amount / usd_rate
                    usdt_addr = get_setting("usdt_address", "YOUR_USDT_TRC20_ADDRESS_HERE")
                    await update.message.reply_text(
                        f"💰 المبلغ: {amount:.0f} ج.م ≈ ${usd_amount:.2f} USDT\n\n"
                        f"🅱️ عنوان USDT TRC20:\n"
                        f"<code>{usdt_addr}</code>\n\n"
                        f"📱 بعد التحويل، ارسل رقم المحفظة/التفاصيل هنا للتأكيد:",
                        parse_mode="HTML"
                    )
            except ValueError:
                await update.message.reply_text("❌ لازم رقم!")
            return
        elif step == "phone":
            sender_info = text.strip()
            amount = context.user_data.get("recharge_amount", 0)
            method = context.user_data.get("recharge_method", "wallet")
            recharge_id = create_recharge(user.id, amount, sender_info)
            await notify_admins_recharge(context, user, amount, sender_info, recharge_id)
            context.user_data.pop("recharge_flow", None)
            context.user_data.pop("recharge_step", None)
            context.user_data.pop("recharge_amount", None)
            context.user_data.pop("recharge_method", None)
            await update.message.reply_text(
                f"⏳ تم إرسال طلب الشحن للأدمن!\n"
                f"💰 المبلغ: {amount:.0f} ج.م\n"
                f"📱 التفاصيل: {sender_info}\n\n"
                f"✅ هنرد عليك في خلال دقايق."
            )
            return

    if context.user_data.get("admin_delivering_order"):
        delivery_step = context.user_data.get("admin_delivery_step")
        order_id = context.user_data.get("admin_delivery_order_id")
        if delivery_step == "email":
            context.user_data["admin_delivery_email"] = text.strip()
            context.user_data["admin_delivery_step"] = "password"
            await update.message.reply_text(f"📦 تسليم حساب — الطلب #{order_id}\n\n✍️ الخطوة 2/2 — ارسل الباسورد:")
            return
        elif delivery_step == "password":
            email = context.user_data.pop("admin_delivery_email", "")
            password = text.strip()
            order = get_order(order_id)
            if order:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE orders SET delivered_email = ?, delivered_password = ?, status = 'completed' WHERE id = ?",
                    (email, password, order_id)
                )
                conn.commit()
                conn.close()
                update_product_stock(order[2], order[3])
                increment_product_sales(order[2], order[3])
                try:
                    await context.bot.send_message(
                        chat_id=order[1],
                        text=(
                            f"✅ تم تأكيد طلبك وتسليم الحساب!\n\n"
                            f"🛍 الطلب رقم: #{order_id}\n"
                            f"📧 الإيميل: <code>{html.escape(email)}</code>\n"
                            f"🔑 الباسورد: <code>{html.escape(password)}</code>\n\n"
                            f"🎉 استمتع بالخدمة!"
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user: {e}")
            context.user_data.pop("admin_delivering_order", None)
            context.user_data.pop("admin_delivery_order_id", None)
            context.user_data.pop("admin_delivery_step", None)
            await update.message.reply_text(f"✅ تم تسليم الطلب #{order_id}")
            return

    # Main menu buttons
    if text == "📦 المنتجات":
        await products_handler(update, context)
        return
    elif text == "🏠 الرئيسية":
        await main_menu_handler(update, context)
        return
    elif text == "🔐 لوحة التحكم المتقدمة":
        if is_admin(user.id) or is_admin_session_active(user.id):
            context.user_data["admin_mode"] = True
            context.user_data["admin_state"] = "menu"
            await update.message.reply_text("🔐 أهلاً بك في لوحة تحكم الأدمن، الإجراء مطلوب:", reply_markup=admin_dashboard_keyboard())
        else:
            await update.message.reply_text("❌ ممنوع دخول هذه اللوحة!", reply_markup=main_menu_keyboard(user.id))
        return

    # Default fallback
    await update.message.reply_text("👇 اختر من القائمة التي تحت:", reply_markup=main_menu_keyboard(user.id))


# ==================== MAIN ENTRY POINT ====================
def main():
    init_db()
    migrate_db()

    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("exit", exit_admin))

    # Callbacks (must be before MessageHandler)
    application.add_handler(CallbackQueryHandler(callback_handler))

    # Photos
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # Text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()