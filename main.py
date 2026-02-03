from flask import Flask, render_template, request, jsonify, redirect, session, flash
from supabase import create_client, Client
from yookassa import Configuration, Payment
import os
import secrets
import uuid
import json
from datetime import datetime
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

products_cache = None
cache_time = None
CACHE_DURATION = 86400

Configuration.account_id = os.environ.get('YOOKASSA_SHOP_ID', 'ВАШ_SHOP_ID')
Configuration.secret_key = os.environ.get('YOOKASSA_SECRET_KEY', 'ВАШ_SECRET_KEY')

# Поулчение значений ключей из переменных окружения
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://euhsbrbgukjkwpqkngqh.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1aHNicmJndWtqa3dwcWtuZ3FoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzcwNjYzNiwiZXhwIjoyMDgzMjgyNjM2fQ.yZdaKqwMFnvM9QubhLCYFTLrTipc2k9h7QKF6TkzeDk')
supabase = None

# Подключение к супабазе, если ключи получены, то создается клиент-объект для взаимодействия с бд
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        print("Supabase ключи не установлены")
except Exception as e:#(ошибка здесь)
    print(f"Ошибка подключения к Supabase: {e}")
    supabase = None


# Главная
@app.route("/")
def index():
    return render_template("index.html")

# Магазин
@app.route('/shop')
def shop():
    global products_cache, cache_time
    
    # старый кэш, если еще не очищен, берется здесь
    if products_cache and cache_time and (datetime.now() - cache_time).seconds < CACHE_DURATION:
        products = products_cache
    else:
        if supabase:
            response = supabase.table("items").select("*").execute()
            products = response.data
            # сохранение кэша
            products_cache = products
            cache_time = datetime.now()
    return render_template('shop.html', products=products)

@app.route("/cart")
def cart():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    return render_template("cart.html")

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

@app.route('/api/update_delivery', methods=['POST'])
def update_delivery():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    
    try:
        data = request.json
        name = data.get('name', '').strip()
        surname = data.get('surname', '').strip()
        cdek_address = data.get('cdek_address', '').strip()
        
        if not all([name, surname, cdek_address]):
            return jsonify({'success': False, 'error': 'Все поля обязательны'})
        
        session['user_name'] = name
        session['user_surname'] = surname
        session['user_cdek_address'] = cdek_address

        if supabase:
            try:
                response = supabase.table('users')\
                    .update({
                        'first_name': name,
                        'last_name': surname,
                        'cdek_address': cdek_address,
                        'updated_at': datetime.now().isoformat()
                    })\
                    .eq('id', session['user_id'])\
                    .execute()
                
                if response.data:
                    print(f"Данные пользователя {session['user_id']} обновлены")
                else:
                    print(f"Пользователь {session['user_id']} не найден в БД")
                    
            except Exception as db_error:
                print(f" Ошибка обновления БД: {db_error}")
        
        return jsonify({
            'success': True,
            'message': 'Данные обновлены',
            'updated_session': True
        })
        
    except Exception as e:
        print(f"Ошибка обновления доставки: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка сервера'
        })

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
        
        return render_template('product.html', product=product)
    except Exception as e:
        print(f"Ошибка: {e}")
        return render_template('product.html', product=None)

@app.route('/api/cart', methods=['GET'])
def get_cart():
    return jsonify({
        'success': True,
        'cart': []
    })

@app.route('/api/items', methods=['GET'])
def get_all_items():
    try:
        if supabase:
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

@app.route('/create_real_payment', methods=['POST'])
def create_real_payment():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Требуется авторизация'})

        data = request.json
        amount = float(data.get('amount', 0))
        items = data.get('items', [])
        
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Неверная сумма'})
        
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        order_id = None
        if supabase:
            try:
                order_data = {
                    'user_id': session['user_id'],
                    'order_number': order_number,
                    'total_amount': amount,
                    'status': 'pending',
                    'items': json.dumps(items, ensure_ascii=False),
                    'shipping_address': session.get('user_cdek_address', ''),
                    'payment_status': 'waiting'
                }
                
                response = supabase.table('orders').insert(order_data).execute()
                if response.data:
                    saved_order = response.data[0]
                    order_id = saved_order['id']
                    print(f"✅ Заказ {order_number} сохранен в БД (ID: {order_id})")
            except Exception as db_error:
                print(f" Ошибка БД: {db_error}")

        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"{request.host_url}payment_success?order={order_number}"
            },
            "description": f"Заказ #{order_number}",
            "capture": True,
            "metadata": {
                "order_id": order_id or order_number,
                "order_number": order_number,
                "user_id": session['user_id']
            }
        }, str(uuid.uuid4()))

        if supabase and order_id:
            supabase.table('orders').update({
                'payment_id': payment.id,
                'updated_at': datetime.now().isoformat()
            }).eq('id', order_id).execute()
        
        session['yookassa_payment_id'] = payment.id
        session['current_order'] = order_number
        
        return jsonify({
            'success': True,
            'payment_id': payment.id,
            'confirmation_url': payment.confirmation.confirmation_url,
            'order_number': order_number,
            'order_id': order_id or order_number
        })
        
    except Exception as e:
        print(f"Ошибка создания платежа: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/payment_success')
def payment_success():
    order_number = request.args.get('order', '')
    
    if not order_number:
        flash('Информация о заказе не найдена', 'error')
        return redirect('/shop')
    
    payment_id = session.get('yookassa_payment_id', '')
    
    try:
        if payment_id:
            payment = Payment.find_one(payment_id)
            
            if payment.status == 'succeeded':
                if supabase:
                    supabase.table('orders').update({
                        'status': 'paid',
                        'payment_status': 'succeeded',
                        'updated_at': datetime.now().isoformat()
                    }).eq('order_number', order_number).execute()
                
                flash(f'Оплата прошла успешно! Заказ #{order_number} оформлен.', 'success')

                session.pop('yookassa_payment_id', None)
                session.pop('current_order', None)

                return render_template('real_payment_success.html',
                    order_number=order_number,
                    amount=payment.amount.value if payment.amount else 0,
                    payment_id=payment_id)

        flash('Платеж не завершен или ожидает подтверждения', 'warning')
        return redirect('/my_orders')
        
    except Exception as e:
        print(f"Ошибка проверки платежа: {e}")
        flash('Ошибка проверки статуса платежа', 'error')
        return redirect('/my_orders')

@app.route('/payment_webhook', methods=['POST'])
def payment_webhook():
    try:
        data = request.json
        event = data.get('event', '')
        payment_data = data.get('object', {})
        
        print(f" Вебхук от ЮKassa: {event}")
        
        if event == 'payment.succeeded':
            payment_id = payment_data.get('id')
            order_number = payment_data.get('metadata', {}).get('order_number', '')
            user_id = payment_data.get('metadata', {}).get('user_id', '')
            
            if order_number and supabase:
                supabase.table('orders').update({
                    'status': 'paid',
                    'payment_status': 'succeeded',
                    'updated_at': datetime.now().isoformat()
                }).eq('order_number', order_number).execute()
                
                print(f" Вебхук: Заказ {order_number} оплачен")
                
                # TODO: Отправка email пользователю
                # send_order_email(user_id, order_number)
        
        elif event == 'payment.canceled':
            order_number = payment_data.get('metadata', {}).get('order_number', '')
            if order_number and supabase:
                supabase.table('orders').update({
                    'status': 'cancelled',
                    'payment_status': 'canceled',
                    'updated_at': datetime.now().isoformat()
                }).eq('order_number', order_number).execute()
                
                print(f"Вебхук: Заказ {order_number} отменен")
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f" Ошибка в вебхуке: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/check_payment_status/<payment_id>')
def check_payment_status(payment_id):
    try:
        payment = Payment.find_one(payment_id)
        return jsonify({
            'status': payment.status,
            'paid': payment.paid,
            'amount': payment.amount.value if payment.amount else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/real_payment_success')
def real_payment_success():
    order_number = session.get('current_order', '')
    if not order_number:
        return redirect('/shop')
    
    return render_template('real_payment_success.html',order_number=order_number)

@app.route('/api/my_orders')
def get_my_orders():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    
    try:
        if supabase:
            response = supabase.table('orders')\
                .select('*')\
                .eq('user_id', session['user_id'])\
                .order('created_at', desc=True)\
                .execute()
            
            orders = response.data
        else:
            # Тестовые данные
            orders = [{
                'id': 'test_order_1',
                'order_number': 'TEST-20241201-ABC123',
                'total_amount': 1899,
                'status': 'paid',
                'items': '[{"name": "Футболка", "price": 1899, "quantity": 1}]',
                'shipping_address': 'г. Москва',
                'created_at': '2024-12-01T10:00:00'
            }]
        
        return jsonify({
            'success': True,
            'orders': orders
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/my_orders')
def my_orders():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect('/login')
    return render_template('my_orders.html')

@app.route('/requisites')
def requisites():
    return render_template('requisites.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)