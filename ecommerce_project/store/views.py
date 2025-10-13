from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Order, OrderItem
from .forms import RegisterForm, CheckoutForm
from .cart import Cart

def home(request):
    products = Product.objects.all()[:8] 
    return render(request, 'store/home.html', {'products': products})
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            hashed_password = make_password(password)
            try:
                if User.objects.filter(username=username).exists():
                    messages.error(request, "Username is already taken.")
                    return render(request, 'store/register.html', {'form': form})
                if User.objects.filter(email=email).exists():
                    messages.error(request, "Email is already registered.")
                    return render(request, 'store/register.html', {'form': form})
                user = User.objects.create(
                    username=username,
                    email=email,
                    password=hashed_password
                )
                user.save()
                login(request, user) 
                messages.success(request, "Registration successful! You are now logged in.")
                return redirect('store:home') 
            except Exception as e:
                print("Error:", e)
                messages.error(request, "An error occurred during registration. Please try again.")
                return render(request, 'store/register.html', {'form': form})
        else:
            messages.error(request, "Please correct the errors below.")
            return render(request, 'store/register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Attempting login for user: {username}") 
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print(f"Login successful for user: {username}") 
            login(request, user)
            return redirect('store:home')
        else:
            print(f"Login failed for user: {username}") 
            return render(request, 'store/login.html', {'error': 'Invalid Username or Password...'})
    return render(request, 'store/login.html')
def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('store:home')
def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)  
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    selected_category = None
    if category_slug:
        if category_slug == 'new-arrivals':
            products = products.order_by('-created_at')  
        elif category_slug == 'festive-sale':
            products = products.filter(is_on_sale=True) 
        else:
            selected_category = Category.objects.filter(slug=category_slug).first()
            if selected_category:
                products = products.filter(category=selected_category)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    context = {
        'categories': categories,
        'products': products,
        'selected_category': category_slug 
    }
    return render(request, 'store/product_list.html', context)
def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart_items = request.session.get('cart', [])
    wishlist_items = request.session.get('wishlist', [])
    context = {
        'product': product,
        'cart_items': cart_items,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'store/product_detail.html', context)
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1, update_quantity=False)
    messages.success(request, f"Added {product.name} to cart.")
    return redirect('store:product_detail', product_id=product.id)
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"Removed {product.name} from cart")
    return redirect('store:cart_detail')
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'store/cart_detail.html', {'cart': cart})
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('store:product_list')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.total = cart.get_total_price()
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
                item['product'].inventory = max(0, item['product'].inventory - item['quantity'])
                item['product'].save()
            order.payment_id = 'PAYMENT_PLACEHOLDER'
            order.status = 'processing'
            order.save()
            cart.clear()
            messages.success(request, f'Order #{order.id} placed successfully.')
            return redirect('store:order_detail_with_id', order_id=order.id)

    else:
        form = CheckoutForm(initial={'email': request.user.email if request.user.is_authenticated else ''})
    return render(request, 'store/checkout.html', {'cart': cart, 'form': form})
@login_required
def order_detail(request, order_id=None):
    if request.method == 'POST' and 'cancel_order' in request.POST:
        cancel_order_id = request.POST.get('cancel_order')
        cancel_order = get_object_or_404(Order, id=cancel_order_id, user=request.user)
        cancel_order.status = 'cancelled'
        cancel_order.save()
        messages.success(request, f"Order #{cancel_order.id} has been cancelled successfully.")
        return redirect('store:order_detail') 
    orders = Order.objects.filter(user=request.user).exclude(status='cancelled')
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        for item in order.items.all():
            item.total_price = item.quantity * item.price
    else:
        order = None
    return render(request, 'store/order_detail.html', {
        'orders': orders,
        'current_order': order
    })
def order_success(request):
    order_id = request.GET.get('order_id')
    order = Order.objects.get(id=order_id)
    return render(request, 'store/order_success.html', {'order': order})


@require_POST
def wishlist_toggle(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    product_id_str = str(product.id)
    
    if product_id_str in cart.wishlist:
        cart.remove_from_wishlist(product)
    else:
        cart.add_to_wishlist(product)
    
    return redirect('store:product_detail', product_id=product.id)

def wishlist_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove_from_wishlist(product) 
    return redirect('store:wishlist_detail')
def wishlist_detail(request):
    cart = Cart(request)
    wishlist_items = list(cart.iter_wishlist())  
    return render(request, 'store/wishlist_detail.html', {
        'wishlist': wishlist_items
    })


def buy_now(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1, update_quantity=False)
    return redirect('store:checkout')