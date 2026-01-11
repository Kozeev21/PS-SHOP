// Функции для работы с корзиной
function updateCartButton() {
    let total = 0;
    for (let key in localStorage) {
        if (key.startsWith('product_quantity_')) {
            total += parseInt(localStorage.getItem(key)) || 0;
        }
    }
    
    const cartButton = document.getElementById('cart-button');
    const cartCount = document.getElementById('cart-count');
    
    if (cartButton) {
        cartButton.textContent = total === 0 ? '🛒 Корзина' : `🛒 Корзина (${total})`;
    }
    if (cartCount) {
        cartCount.textContent = total;
    }
}

function goToCart() {
    window.location.href = "/cart";
}

function goToProductPage(productId) {
    window.location.href = `/product/${productId}`;
}

function addToCart(productId, productName, productPrice, productImg) {
    let quantity = parseInt(localStorage.getItem(`product_quantity_${productId}`)) || 0;
    quantity += 1;
    
    // Сохраняем все данные товара
    localStorage.setItem(`product_quantity_${productId}`, quantity);
    localStorage.setItem(`product_${productId}`, productName);
    localStorage.setItem(`product_price_${productId}`, productPrice);
    localStorage.setItem(`product_img_${productId}`, productImg || '');
    
    // Обновляем отображение количества
    updateQuantityDisplay(productId, quantity);
    updateCartButton();
    showNotification(`${productName} добавлен в корзину!`);
}

// Обновление отображения количества
function updateQuantityDisplay(productId, quantity) {
    const quantitySpan = document.querySelector(`.quantity-display[data-id="${productId}"]`);
    if (quantitySpan) {
        quantitySpan.textContent = quantity;
    }
}

function showNotification(message) {
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Добавляем стили для анимации
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Удаляем через 3 секунды
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

function clearCart() {
    if (confirm('Очистить всю корзину?')) {
        // Удаляем только товарные данные
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('product_')) {
                keysToRemove.push(key);
            }
        }
        
        keysToRemove.forEach(key => localStorage.removeItem(key));
        
        // Обновляем отображение
        document.querySelectorAll('.quantity-display').forEach(span => {
            span.textContent = '0';
        });
        
        updateCartButton();
        showNotification('Корзина очищена!');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    updateCartButton();
    
    // Восстанавливаем количество для каждого товара
    document.querySelectorAll('.quantity-display').forEach(span => {
        const productId = span.dataset.id;
        const quantity = parseInt(localStorage.getItem(`product_quantity_${productId}`)) || 0;
        span.textContent = quantity;
    });
    
    // Назначаем обработчики для кнопок + (inline в HTML)
    document.querySelectorAll('.increase').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productCard = this.closest('.product-card');
            const productId = productCard.dataset.id;
            const productName = productCard.dataset.name;
            const productPrice = productCard.dataset.price || 0;
            const productImg = productCard.dataset.img || '';
            
            // Получаем текущее количество
            let quantity = parseInt(localStorage.getItem(`product_quantity_${productId}`)) || 0;
            quantity += 1;
            
            // Сохраняем
            localStorage.setItem(`product_quantity_${productId}`, quantity);
            localStorage.setItem(`product_${productId}`, productName);
            localStorage.setItem(`product_price_${productId}`, productPrice);
            localStorage.setItem(`product_img_${productId}`, productImg);
            
            // Обновляем отображение
            const quantitySpan = document.querySelector(`.quantity-display[data-id="${productId}"]`);
            if (quantitySpan) {
                quantitySpan.textContent = quantity;
            }
            
            updateCartButton();
            showNotification(`${productName} добавлен в корзину!`);
        });
    });
    
    // Назначаем обработчики для кнопок - (inline в HTML)
    document.querySelectorAll('.decrease').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productCard = this.closest('.product-card');
            const productId = productCard.dataset.id;
            const productName = productCard.dataset.name;
            
            // Получаем текущее количество
            let quantity = parseInt(localStorage.getItem(`product_quantity_${productId}`)) || 0;
            
            if (quantity > 0) {
                quantity -= 1;
                localStorage.setItem(`product_quantity_${productId}`, quantity);
                
                // Если количество стало 0, не удаляем данные товара полностью
                // чтобы сохранить название и цену для корзины
                
                // Обновляем отображение
                const quantitySpan = document.querySelector(`.quantity-display[data-id="${productId}"]`);
                if (quantitySpan) {
                    quantitySpan.textContent = quantity;
                }
                
                updateCartButton();
                showNotification('Количество уменьшено');
            }
        });
    });
});

// Функции для страницы товара
function increaseQuantity(productId, productName) {
    let quantity = parseInt(localStorage.getItem(`product_quantity_${productId}`)) || 0;
    quantity += 1;
    localStorage.setItem(`product_quantity_${productId}`, quantity);
    localStorage.setItem(`product_${productId}`, productName);
    updateCartButton();
}

function decreaseQuantity(productId) {
    let quantity = parseInt(localStorage.getItem(`product_quantity_${productId}`)) || 0;
    if (quantity > 0) {
        quantity -= 1;
        localStorage.setItem(`product_quantity_${productId}`, quantity);
        updateCartButton();
    }
}

// Глобальные функции (доступны из HTML onclick)
window.addToCart = addToCart;
window.clearCart = clearCart;
window.goToCart = goToCart;
window.goToProductPage = goToProductPage;
window.increaseQuantity = increaseQuantity;
window.decreaseQuantity = decreaseQuantity;
window.updateCartButton = updateCartButton;