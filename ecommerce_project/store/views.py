from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
import re
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from httpcore import request
from .models import Product, Category, Order, OrderItem,RegisterData
from .forms import CustomUserForm, CheckoutForm
from .cart import Cart

def home(request):
    products = Product.objects.all()[:8]  # show top 8 items on home
    return render(request, 'store/home.html', {'products': products})

def register(request):
    if request.method == 'POST':
        # Retrieve data from the form
        name = request.POST.get('name')
        email = request.POST.get('email')
        number = request.POST.get('number')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Email validation for Gmail format
        email_regex = r'^[a-zA-Z0-9_.+-]+@gmail\.com$'
        
        if not re.match(email_regex, email):
            # If the email is not a valid Gmail address, silently return the form
            return render(request, 'store/login.html', {'show_register': True, 'error': 'Please enter a valid Gmail address.'})

        # Save to the custom RegisterData model if the email is valid
        try:
            # Check if username already exists
            if RegisterData.objects.filter(username=username).exists():
                return render(request, 'store/login.html', {'show_register': True, 'error': 'Username already taken.'})
            
            # Check if email already exists
            if RegisterData.objects.filter(email=email).exists():
                return render(request, 'store/login.html', {'show_register': True, 'error': 'Email already registered.'})

            # Create new user in the RegisterData model
            new_user = RegisterData.objects.create(
                name=name,
                email=email,
                number=number,
                username=username,
                password=password
            )
            return redirect('login')  # Redirect to login page after successful registration

        except Exception as e:
            print("Error:", e)
            return render(request, 'store/register.html', {'show_register': True, 'error': 'An error occurred. Please try again.'})

    else:
        return render(request, 'store/register.html', {'show_register': True})


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Check if user exists with the provided email or username
            user = RegisterData.objects.get(username=username)
        except RegisterData.DoesNotExist:
            user = None

        if user is not None and user.password == password:
            # Simulate login
            return redirect('home')
        else:
            return render(request, 'store/login.html', {'error': 'Invalid Username or Password...'})

    return render(request, 'store/login.html')


def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('store/home')


# Product listing


def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)  # only active products

    # Get filters from query parameters
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # CATEGORY FILTER
    selected_category = None
    if category_slug:
        if category_slug == 'new-arrivals':
            products = products.order_by('-created_at')  # latest products
        elif category_slug == 'festive-sale':
            products = products.filter(is_on_sale=True)  # requires is_on_sale field
        else:
            # Safe filter: return None if slug not found
            selected_category = Category.objects.filter(slug=category_slug).first()
            if selected_category:
                products = products.filter(category=selected_category)

    # PRICE FILTER
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    context = {
        'categories': categories,
        'products': products,
        'selected_category': category_slug  # for template highlighting
    }
    return render(request, 'store/product_list.html', context)

# Product detail
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    cart = Cart(request)

    cart_items = [item['product'].id for item in cart]
    wishlist_items = [item['product'].id for item in cart.iter_wishlist()]  # ✅ get wishlist product ids

    return render(request, 'store/product_detail.html', {
        'product': product,
        'cart_items': cart_items,
        'wishlist_items': wishlist_items,
    })


# Cart views
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1, update_quantity=False)
    
    # Show success message for "Add to Cart"
    messages.success(request, f"Added {product.name} to cart.")
    
    return redirect('store:product_detail', id=product.id)


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"Removed {product.name} from cart")
    return redirect('store:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'store/cart_detail.html', {'cart': cart})




# Checkout & Order processing
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
            return redirect('store:order_detail', order_id=order.id)
    else:
        form = CheckoutForm(initial={'email': request.user.email if request.user.is_authenticated else ''})
    return render(request, 'store/checkout.html', {'cart': cart, 'form': form})


# Order detail
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user and request.user != order.user and not request.user.is_staff:
        messages.error(request, 'You cannot view this order.')
        return redirect('store:product_list')
    return render(request, 'store/order_detail.html', {'order': order})

@require_POST
def wishlist_toggle(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    product_id_str = str(product.id)
    
    if product_id_str in cart.wishlist:
        cart.remove_from_wishlist(product)
    else:
        cart.add_to_wishlist(product)
    
    return redirect('store:product_detail', id=product.id)

def wishlist_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove_from_wishlist(product)  # ✅ Remove item from wishlist
    return redirect('store:wishlist_detail')  # ✅ Redirect to wishlist page

# View Wishlist
def wishlist_detail(request):
    cart = Cart(request)
    wishlist_items = list(cart.iter_wishlist())  # 👈 MAKE SURE THIS IS A LIST
    return render(request, 'store/wishlist_detail.html', {
        'wishlist': wishlist_items
    })


def buy_now(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Adding the product to the cart with quantity = 1 (or you can get it from the request)
    cart.add(product=product, quantity=1, update_quantity=False)
    
    # Redirecting to checkout page immediately
    return redirect('store:checkout')