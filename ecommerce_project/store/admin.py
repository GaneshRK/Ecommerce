from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'inventory', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fields = ('category', 'name', 'slug', 'description', 'price', 'inventory', 'image', 'is_active')  # Explicit field order
