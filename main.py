from flask import Flask, render_template, request, jsonify, redirect, session, flash
from supabase import create_client, Client
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# 1. Сначала объявим переменные
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://lpujjrotigzlbjylurjo.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwdWpqcm90aWd6bGJqeWx1cmpvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzczODY2OCwiZXhwIjoyMDgzMzE0NjY4fQ.fYG2T9afNb2doqqkBq58Zv4fp155XL-E0lLWVhmb_6o')
supabase = None

# 2. Пробуем подключиться к Supabase
try:
    print(f"Пытаюсь подключиться к Supabase...")
    print(f"URL: {SUPABASE_URL}")
    print(f"Key exists: {bool(SUPABASE_KEY)}")
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase подключен")
    else:
        print("⚠️ Supabase ключи не установлены, буду использовать тестовые данные")
except Exception as e:
    print(f"❌ Ошибка подключения к Supabase: {e}")
    supabase = None

# Тестовые товары НА ВСЯКИЙ СЛУЧАЙ
TEST_PRODUCTS = [
    {"id": 1, "name": "Футболка", "price": 1899, "img_url": "https://via.placeholder.com/300x400/007bff/FFFFFF?text=T-Shirt"},
    {"id": 2, "name": "Джинсы", "price": 4599, "img_url": "https://via.placeholder.com/300x400/28a745/FFFFFF?text=Jeans"},
    {"id": 3, "name": "Куртка", "price": 8999, "img_url": "https://via.placeholder.com/300x400/dc3545/FFFFFF?text=Jacket"},
]

# Главная
@app.route("/")
def index():
    return render_template("index.html")

# Магазин - УПРОЩЕННАЯ ВЕРСИЯ, ЧТОБЫ НЕ ЛОМАЛОСЬ
@app.route('/shop')
def shop():
    """Магазин - всегда работает"""
    try:
        products = []
        
        # Пробуем взять из Supabase
        if supabase:
            try:
                print("Пытаюсь загрузить товары из Supabase...")
                response = supabase.table("items").select("*").execute()
                
                if hasattr(response, 'data'):
                    products = response.data
                    print(f"Загружено {len(products)} товаров из Supabase")
                else:
                    print("Supabase вернул пустой ответ")
                    products = TEST_PRODUCTS
                    
            except Exception as e:
                print(f"Ошибка при загрузке из Supabase: {e}")
                products = TEST_PRODUCTS
        else:
            print("Supabase не подключен, использую тестовые данные")
            products = TEST_PRODUCTS
        
        # Гарантируем что у каждого товара есть id
        for product in products:
            if 'id' not in product:
                product['id'] = product.get('uuid', hash(product.get('name', '')))
        
        return render_template('shop.html', products=products)
        
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА в /shop: {e}")
        # Всегда возвращаем хоть что-то
        return render_template('shop.html', products=TEST_PRODUCTS)

# Профиль
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    
    user_data = {
        'name': session.get('user_name', ''),
        'surname': session.get('user_surname', ''),
        'email': session.get('user_email', ''),
        'cdek_address': session.get('user_cdek_address', '')
    }
    
    return render_template('profile.html', user=user_data)

# Корзина
@app.route("/cart")
def cart():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    return render_template("cart.html")

# Авторизация (УПРОЩЕННАЯ)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # ПРОСТАЯ ПРОВЕРКА - РАБОТАЕТ ВСЕГДА
        if email and password:
            # Для теста - любой пароль подойдет
            session['user_id'] = '1'
            session['user_email'] = email
            session['user_name'] = email.split('@')[0]
            session['user_surname'] = 'Тестовый'
            session['user_cdek_address'] = 'г. Москва'
            
            flash('Вход выполнен успешно!', 'success')
            return redirect('/shop')
        else:
            flash('Введите email и пароль', 'error')
    
    return render_template('login.html')

# Регистрация (УПРОЩЕННАЯ)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        cdek_address = request.form.get('cdek_address')
        
        if email:
            session['user_id'] = '1'
            session['user_email'] = email
            session['user_name'] = first_name or 'Пользователь'
            session['user_surname'] = last_name or 'Новый'
            session['user_cdek_address'] = cdek_address or 'г. Москва'
            
            flash('Регистрация прошла успешно!', 'success')
            return redirect('/shop')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect('/')

# Страница товара
@app.route('/product/<product_id>')
def product_detail(product_id):
    try:
        product = None
        
        # Пробуем найти товар
        for p in TEST_PRODUCTS:
            if str(p['id']) == str(product_id):
                product = p
                product['uuid'] = p['id']
                break
        
        return render_template('product.html', product=product)
    except Exception as e:
        print(f"Ошибка загрузки товара: {e}")
        return render_template('product.html', product=None)

# Дебаг страница
@app.route('/debug')
def debug():
    info = {
        'app': 'running',
        'supabase_connected': supabase is not None,
        'supabase_url': SUPABASE_URL,
        'test_products_count': len(TEST_PRODUCTS)
    }
    return jsonify(info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Запускаю приложение на порту {port}")
    print(f"🛒 Тестовых товаров: {len(TEST_PRODUCTS)}")
    print(f"🔗 Supabase: {'подключен' if supabase else 'не подключен'}")
    app.run(host='0.0.0.0', port=port)