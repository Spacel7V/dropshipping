from django.shortcuts import render, redirect, reverse
import stripe
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import *
from .utils import *
from .cart import Cart
from .forms import *
from django.contrib import messages

stripe.api_key = settings.STRIPE_SECRET_KEY

def shop_view(request):
    products_list = stripe.Product.list()
    products = []

    for product in products_list['data']:
        if product.get('metadata', {}).get('category') == "shop":
            products.append(get_product_details(product))

    return render(request, 'a_stripe/shop.html', {'products': products})

def product_view(request, product_id):
    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product)

    cart = Cart(request)
    product_details['in_cart'] = product_id in cart.cart_session

    return render(request, 'a_stripe/product.html', {'product': product_details})

def add_to_cart(request, product_id):
    cart = Cart(request)
    cart.add(product_id)

    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product)
    product_details['in_cart'] = product_id in cart.cart_session

    response = render(request, 'a_stripe/partials/cart-button.html', {'product': product_details})
    response['HX-Trigger'] = 'hx_menu_cart'
    return response

def hx_menu_cart(request):
    return render(request, 'a_stripe/partials/menu-cart.html')

def cart_view(request):
    quantity_range = list(range(1, 11))
    return render(request, 'a_stripe/cart.html', {'quantity_range': quantity_range})

def update_checkout(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    cart = Cart(request)
    cart.add(product_id, quantity)

    product = stripe.Product.retrieve(product_id)
    product_details = get_product_details(product)
    product_details['total_price'] = product_details['price'] * quantity

    response = render(request, 'a_stripe/partials/checkout-total.html', {'product': product_details})
    response['HX-Trigger'] = 'hx_menu_cart'
    return response

def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect('cart')

def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, "Votre panier est vide.")
        return redirect('cart')

    shipping_info_instance = None
    initial_data = {}

    if request.user.is_authenticated:
        shipping_info_instance = ShippingInfo.objects.filter(user=request.user).first()
        if not shipping_info_instance and request.user.email:
            initial_data['email'] = request.user.email
    else:
        shipping_info_id = request.session.get('shipping_info_id')
        if shipping_info_id:
            shipping_info_instance = ShippingInfo.objects.filter(
                pk=shipping_info_id,
                user__isnull=True,
            ).first()

    if request.method == 'POST':
        form = ShippingForm(request.POST, instance=shipping_info_instance)
        if form.is_valid():
            shipping_info = form.save(commit=False)
            email = form.cleaned_data.get('email')
            shipping_info.email = email.lower() if email else None

            if request.user.is_authenticated:
                shipping_info.user = request.user
            else:
                shipping_info.user = None

            shipping_info.save()

            if not request.user.is_authenticated:
                request.session['shipping_info_id'] = shipping_info.id

            checkout_session = create_checkout_session(cart, shipping_info.email)

            CheckoutSession.objects.create(
                checkout_id = checkout_session.id,
                shipping_info = shipping_info,
                total_cost = cart.get_total_cost()
            )
            
            return redirect(checkout_session.url, code=303)
    else:
        form = ShippingForm(instance=shipping_info_instance, initial=initial_data)

    return render(request, 'a_stripe/checkout.html', {'form': form})

def payment_successful(request):
    checkout_session_id = request.GET.get('session_id', None)
    
    if checkout_session_id:
        session = stripe.checkout.Session.retrieve(checkout_session_id)
        customer_id = session.customer
        customer = stripe.Customer.retrieve(customer_id)
        
        if settings.CART_SESSION_ID in request.session:
            del request.session[settings.CART_SESSION_ID]
            
        if settings.DEBUG:
            checkout = CheckoutSession.objects.get(checkout_id=checkout_session_id)
            checkout.has_paid = True
            checkout.save()
    
    return render(request, 'a_stripe/payment_successful.html', {'customer': customer})

def payment_cancelled(request):
    return render(request, 'a_stripe/payment_cancelled.html')

@require_POST
@csrf_exempt
def stripe_webhook(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    signature_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try : 
        event = stripe.Webhook.construct_event(
            payload, signature_header, endpoint_secret
        )
    except:
        return HttpResponse(status=400)
    
    if event['type'] == 'chekout.session.completed':
        session = event['data']['object']
        checkout_session_id = session.get('id')
        checkout = CheckoutSession.objects.get(checkout_id=checkout_session_id)
        checkout.has_paid = True
        checkout.save()

    return HttpResponse(status=200)
