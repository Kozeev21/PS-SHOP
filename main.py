from flask import Flask, render_template, request, jsonify, redirect, session, flash
from supabase import create_client, Client
import os
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

products_cache = None
cache_time = None
CACHE_DURATION = 300

# Инициализация Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://euhsbrbgukjkwpqkngqh.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1aHNicmJndWtqa3dwcWtuZ3FoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzcwNjYzNiwiZXhwIjoyMDgzMjgyNjM2fQ.yZdaKqwMFnvM9QubhLCYFTLrTipc2k9h7QKF6TkzeDk')
supabase = None

# Пробуем подключиться к Supabase
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase подключен")
    else:
        print("⚠️ Supabase ключи не установлены")
except Exception as e:
    print(f"❌ Ошибка подключения к Supabase: {e}")
    supabase = None

# Тестовые данные (если Supabase не работает)
TEST_PRODUCTS = [
    {"id": 1, "name": "Футболка", "price": 1899, "img_url": "https://via.placeholder.com/300x400/007bff/FFFFFF?text=T-Shirt"},
    {"id": 2, "name": "Джинсы", "price": 4599, "img_url": "https://via.placeholder.com/300x400/28a745/FFFFFF?text=Jeans"},
    {"id": 3, "name": "Куртка", "price": 8999, "img_url": "https://via.placeholder.com/300x400/dc3545/FFFFFF?text=Jacket"},
]

# ВСЕ ПУТИ, КОТОРЫЕ БЫЛИ У ТЕБЯ:

# Главная
@app.route("/")
def index():
    return render_template("index.html")

# Магазин
@app.route('/shop')
def shop():
    global products_cache, cache_time
    
    try:
        # Используем кеш если он есть и не устарел
        if products_cache and cache_time and (datetime.now() - cache_time).seconds < CACHE_DURATION:
            print("✅ Используем кешированные товары")
            products = products_cache
        else:
            if supabase:
                response = supabase.table("items").select("*").execute()
                products = response.data
                # Сохраняем в кеш
                products_cache = products
                cache_time = datetime.now()
                print("✅ Загрузили товары из БД и закешировали")
            else:
                products = TEST_PRODUCTS
        return render_template('shop.html', products=products)
    except Exception as e:
        print(f"Ошибка: {e}")
        return render_template('shop.html', products=TEST_PRODUCTS)
# Корзина
@app.route("/cart")
def cart():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    return render_template("cart.html")

# Оформление заказа (ЧЕКАУТ ЕСТЬ!)
@app.route("/checkout", methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        session.pop('cart_items', None)
        flash('Заказ оформлен! Корзина очищена.', 'success')
        return redirect('/shop')
    
    return render_template("checkout.html")

# О нас
@app.route("/about")
def about():
    return render_template("about.html")

# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            if supabase:
                response = supabase.table('users').select('*').eq('email', email).eq('password', password).execute()
                if response.data:
                    user = response.data[0]
                else:
                    user = None
            else:
                # Тестовый пользователь
                if email == "test@test.com" and password == "test123":
                    user = {'id': 1, 'email': email, 'first_name': 'Тест', 'last_name': 'Пользователь', 'cdek_address': 'г. Москва'}
                else:
                    user = None
            
            if user:
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['user_name'] = user.get('first_name', '')
                session['user_surname'] = user.get('last_name', '')
                session['user_cdek_address'] = user.get('cdek_address', '')
                flash('Вход выполнен успешно!', 'success')
                return redirect('/shop')
            else:
                flash('Неверный email или пароль', 'error')
        except Exception as e:
            flash(f'Ошибка при входе: {str(e)}', 'error')
    
    return render_template('login.html')

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        cdek_address = request.form.get('cdek_address')
        
        if not all([first_name, last_name, email, password, cdek_address]):
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('register.html')
        
        try:
            if supabase:
                check_response = supabase.table('users').select('*').eq('email', email).execute()
                if check_response.data:
                    flash('Пользователь с таким email уже существует', 'error')
                    return render_template('register.html')
                
                user_data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'password': password,
                    'cdek_address': cdek_address
                }
                
                response = supabase.table('users').insert(user_data).execute()
                
                if response.data:
                    user = response.data[0]
                    session['user_id'] = user['id']
                    session['user_email'] = user['email']
                    session['user_name'] = user['first_name']
                    session['user_surname'] = user['last_name']
                    session['user_cdek_address'] = user['cdek_address']
                    flash('Регистрация прошла успешно!', 'success')
                    return redirect('/shop')
            else:
                # Тестовый режим
                session['user_id'] = 1
                session['user_email'] = email
                session['user_name'] = first_name
                session['user_surname'] = last_name
                session['user_cdek_address'] = cdek_address
                flash('Регистрация прошла успешно!', 'success')
                return redirect('/shop')
            
        except Exception as e:
            flash(f'Ошибка при регистрации: {str(e)}', 'error')
    
    return render_template('register.html')

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect('/')

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

# Страница товара (ПРОДУКТ ЕСТЬ!)
@app.route('/product/<product_id>')
def product_detail(product_id):
    try:
        if supabase:
            response = supabase.table("items").select("*").eq("id", product_id).execute()
            if response.data:
                product = response.data[0]
                product['uuid'] = product['id']
            else:
                product = None
        else:
            product = None
            for p in TEST_PRODUCTS:
                if str(p['id']) == str(product_id):
                    product = p
                    product['uuid'] = p['id']
                    break
        
        return render_template('product.html', product=product)
    except Exception as e:
        print(f"Ошибка: {e}")
        return render_template('product.html', product=None)

# API для получения корзины
@app.route('/api/cart', methods=['GET'])
def get_cart():
    return jsonify({
        'success': True,
        'cart': []
    })

# API для товаров
@app.route('/api/items', methods=['GET'])
def get_all_items():
    try:
        if supabase:
            response = supabase.table('items').select('*').execute()
            items = response.data
        else:
            items = TEST_PRODUCTS
            
        return jsonify({
            'success': True,
            'count': len(items),
            'items': items
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)