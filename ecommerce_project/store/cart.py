from decimal import Decimal
from django.conf import settings

CART_SESSION_ID = 'cart'
WISHLIST_SESSION_ID = 'wishlist'

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(CART_SESSION_ID, {})
        self.wishlist = self.session.get(WISHLIST_SESSION_ID, {})
        if not self.cart:
            self.session[CART_SESSION_ID] = self.cart
        if not self.wishlist:
            self.session[WISHLIST_SESSION_ID] = self.wishlist

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}

        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    def add_to_wishlist(self, product):
        product_id = str(product.id)
        if product_id not in self.wishlist:
            self.wishlist[product_id] = {'price': str(product.price)}
            self.save()
    def remove_from_wishlist(self, product):
        product_id = str(product.id)
        if product_id in self.wishlist:
            del self.wishlist[product_id]
            self.save()
    def save(self):
        for product_id, item in self.cart.items():
            if isinstance(item.get('price'), Decimal):
                self.cart[product_id]['price'] = str(item['price'])
        for product_id, item in self.wishlist.items():
            if isinstance(item.get('price'), Decimal):
                self.wishlist[product_id]['price'] = str(item['price'])

        self.session.modified = True

    def __iter__(self):
        from .models import Product

        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            item = self.cart[str(product.id)]
            item['product'] = product
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        if CART_SESSION_ID in self.session:
            del self.session[CART_SESSION_ID]
            self.save()

    def iter_wishlist(self):
        from .models import Product

        product_ids = self.wishlist.keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            product_id = str(product.id)
            wishlist_item = self.wishlist[product_id]
            item = {
                'product': product,
                'price': Decimal(wishlist_item['price']),
            }
            yield item