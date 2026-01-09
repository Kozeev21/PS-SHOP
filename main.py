from flask import Flask, render_template, request, jsonify, redirect, session, flash
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ТЕСТОВЫЕ ДАННЫЕ вместо Supabase
TEST_PRODUCTS = [
    {"id": "1", "name": "Футболка", "price": 1899, "img_url": "https://via.placeholder.com/300x400/007bff/FFFFFF?text=T-Shirt"},
    {"id": "2", "name": "Джинсы", "price": 4599, "img_url": "https://via.placeholder.com/300x400/28a745/FFFFFF?text=Jeans"},
    {"id": "3", "name": "Куртка", "price": 8999, "img_url": "https://via.placeholder.com/300x400/dc3545/FFFFFF?text=Jacket"},
    {"id": "4", "name": "Рубашка", "price": 2499, "img_url": "https://via.placeholder.com/300x400/ffc107/000000?text=Shirt"},
    {"id": "5", "name": "Платье", "price": 5999, "img_url": "https://via.placeholder.com/300x400/17a2b8/FFFFFF?text=Dress"},
    {"id": "6", "name": "Кроссовки", "price": 7999, "img_url": "https://via.placeholder.com/300x400/6f42c1/FFFFFF?text=Sneakers"},
]

# Тестовые пользователи (временно)
TEST_USERS = [
    {"id": "1", "email": "test@test.com", "password": "test123", "first_name": "Иван", "last_name": "Иванов", "cdek_address": "г. Москва, ул. Ленина, д. 1"}
]

# Главная
@app.route("/")
def index():
    return render_template("index.html")

# Магазин
@app.route('/shop')
def shop():
    try:
        # Используем тестовые данные
        return render_template('shop.html', products=TEST_PRODUCTS)
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

# Оформление заказа
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
            # Ищем пользователя в тестовых данных
            user = None
            for u in TEST_USERS:
                if u['email'] == email and u['password'] == password:
                    user = u
                    break
            
            if user:
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
            # Проверяем, нет ли уже такого email
            for user in TEST_USERS:
                if user['email'] == email:
                    flash('Пользователь с таким email уже существует', 'error')
                    return render_template('register.html')
            
            # Создаем нового пользователя
            new_user = {
                'id': str(len(TEST_USERS) + 1),
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                'cdek_address': cdek_address
            }
            
            # В тестовом режиме просто добавляем в список
            TEST_USERS.append(new_user)
            
            session['user_id'] = new_user['id']
            session['user_email'] = new_user['email']
            session['user_name'] = new_user['first_name']
            session['user_surname'] = new_user['last_name']
            session['user_cdek_address'] = new_user['cdek_address']
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
        # Ищем товар в тестовых данных
        product = None
        for p in TEST_PRODUCTS:
            if str(p['id']) == str(product_id):
                product = p
                break
        
        if product:
            # Добавляем uuid для совместимости
            product['uuid'] = product['id']
            return render_template('product.html', product=product)
        else:
            return render_template('product.html', product=None)
    except Exception as e:
        print(f"Ошибка: {e}")
        return render_template('product.html', product=None)

# API для товаров
@app.route('/api/items', methods=['GET'])
def get_all_items():
    try:
        return jsonify({
            'success': True,
            'count': len(TEST_PRODUCTS),
            'items': TEST_PRODUCTS
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)