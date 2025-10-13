from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_page,name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_detail, name='order_detail'),  # for all orders
    path('orders/<int:order_id>/', views.order_detail, name='order_detail_with_id'),
    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('order-success/', views.order_success, name='order_success'),
]

