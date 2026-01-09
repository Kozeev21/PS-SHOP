from flask import Flask, render_template, request, jsonify, redirect, session, flash
from supabase import create_client, Client
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Инициализация Supabase - ДА, ВОТ ТУТ ВСЕ!
SUPABASE_URL = os.environ.get('https://lpujjrotigzlbjylurjo.supabase.co')
SUPABASE_KEY = os.environ.get('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwdWpqcm90aWd6bGJqeWx1cmpvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzczODY2OCwiZXhwIjoyMDgzMzE0NjY4fQ.fYG2T9afNb2doqqkBq58Zv4fp155XL-E0lLWVhmb_6o')

print(f"DEBUG: Supabase URL: {SUPABASE_URL}")
print(f"DEBUG: Supabase Key first 20 chars: {SUPABASE_KEY[:20] if SUPABASE_KEY else 'NOT SET'}")

try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL or KEY not set in environment variables")
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client created successfully")
    
    # Тестовый запрос
    test = supabase.table("items").select("*").limit(1).execute()
    print(f"✅ Test query successful, found {len(test.data)} items")
    
except Exception as e:
    print(f"❌ CRITICAL: Supabase initialization failed: {e}")
    supabase = None
    # Можно выйти с ошибкой
    # import sys
    # sys.exit(1)

# Тестовые данные НА ВСЯКИЙ СЛУЧАЙ
'''TEST_PRODUCTS = [
    {"id": "1", "name": "Футболка", "price": 1899, "img_url": "https://via.placeholder.com/300x400/007bff/FFFFFF?text=T-Shirt"},
    {"id": "2", "name": "Джинсы", "price": 4599, "img_url": "https://via.placeholder.com/300x400/28a745/FFFFFF?text=Jeans"},
    {"id": "3", "name": "Куртка", "price": 8999, "img_url": "https://via.placeholder.com/300x400/dc3545/FFFFFF?text=Jacket"},
]'''

# Главная
@app.route("/")
def index():
    return render_template("index.html")

# Магазин - ПРОСТАЯ ВЕРСИЯ
@app.route('/shop')
def shop():
    try:
        if supabase:
            print("DEBUG: Fetching from Supabase...")
            response = supabase.table("items").select("*").execute()
            products = response.data
            print(f"DEBUG: Got {len(products)} products from Supabase")
        else:
            print("DEBUG: Using test products (supabase is None)")
            products = TEST_PRODUCTS
            
        return render_template('shop.html', products=products)
    except Exception as e:
        print(f"ERROR in /shop: {e}")
        return render_template('shop.html', products=TEST_PRODUCTS)

# Дебаг страница
@app.route('/debug')
def debug():
    info = {
        'supabase_exists': supabase is not None,
        'supabase_url': SUPABASE_URL,
        'supabase_key_exists': bool(SUPABASE_KEY),
        'session_user_id': session.get('user_id'),
    }
    
    if supabase:
        try:
            # Проверяем таблицу items
            items_resp = supabase.table("items").select("*").execute()
            info['items_count'] = len(items_resp.data)
            info['items_sample'] = items_resp.data[:3] if items_resp.data else []
            
            # Проверяем таблицу users
            users_resp = supabase.table("users").select("*").execute()
            info['users_count'] = len(users_resp.data)
            
        except Exception as e:
            info['supabase_error'] = str(e)
    
    return jsonify(info)

# Остальные роуты...
@app.route("/cart")
def cart():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    return render_template("cart.html")

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
                    user = {
                        'id': '1',
                        'email': email,
                        'first_name': 'Тест',
                        'last_name': 'Пользователь',
                        'cdek_address': 'г. Москва'
                    }
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
                # Проверяем, нет ли уже такого email
                check_response = supabase.table('users').select('*').eq('email', email).execute()
                if check_response.data:
                    flash('Пользователь с таким email уже существует', 'error')
                    return render_template('register.html')
                
                # Создаем нового пользователя
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
                # Локальная регистрация для теста
                session['user_id'] = '1'
                session['user_email'] = email
                session['user_name'] = first_name
                session['user_surname'] = last_name
                session['user_cdek_address'] = cdek_address
                flash('Регистрация прошла успешно! (тестовый режим)', 'success')
                return redirect('/shop')
            
        except Exception as e:
            flash(f'Ошибка при регистрации: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect('/')

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
        print(f"Ошибка загрузки товара: {e}")
        return render_template('product.html', product=None)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)