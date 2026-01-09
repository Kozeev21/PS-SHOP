import os
from flask import Flask, render_template, request, jsonify, redirect, session, flash
from supabase import create_client, Client
import secrets

app = Flask(__name__)

# Получаем SECRET_KEY из переменных окружения
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Supabase конфигурация
SUPABASE_URL = os.environ.get('SUPABASE_URL', "https://lpujjrotigzlbjylurjo.supabase.co")
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', "sb_publishable_bb8wQ0vi-c_GClSOOStPvg_EiTwn2Da")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Главная
@app.route("/")
def index():
    return render_template("index.html")

# Магазин
@app.route('/shop')
def shop():
    try:
        response = supabase.table("items").select("*").execute()
        products = response.data
        return render_template('shop.html', products=products)
    except Exception as e:
        print(f"Ошибка: {e}")
        # Тестовые данные
        products = [
            {"id": "1", "name": "Футболка", "price": 1899, "img_url": "https://via.placeholder.com/300x400/007bff/FFFFFF?text=T-Shirt"},
            {"id": "2", "name": "Джинсы", "price": 4599, "img_url": "https://via.placeholder.com/300x400/28a745/FFFFFF?text=Jeans"},
            {"id": "3", "name": "Куртка", "price": 8999, "img_url": "https://via.placeholder.com/300x400/dc3545/FFFFFF?text=Jacket"},
        ]
        return render_template('shop.html', products=products)

# Корзина
@app.route("/cart")
def cart():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    
    # Получаем товары из корзины (из localStorage на клиенте)
    return render_template("cart.html")

# Оформление заказа
@app.route("/checkout", methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        # Здесь будет логика оформления заказа
        # Очищаем сессию после оформления
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
            response = supabase.table('users').select('*').eq('email', email).eq('password', password).execute()
            
            if response.data:
                user = response.data[0]
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['user_name'] = user['first_name']
                session['user_surname'] = user['last_name']
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

# Страница товара
@app.route('/product/<product_id>')
def product_detail(product_id):
    try:
        response = supabase.table("items").select("*").eq("id", product_id).execute()
        
        if response.data:
            product = response.data[0]
            # Добавляем uuid для совместимости с шаблоном
            product['uuid'] = product['id']
            return render_template('product.html', product=product)
        else:
            return render_template('product.html', product=None)
    except Exception as e:
        print(f"Ошибка: {e}")
        return render_template('product.html', product=None)

# API для получения корзины (для AJAX)
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
        response = supabase.table('items').select('*').execute()
        items = response.data
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