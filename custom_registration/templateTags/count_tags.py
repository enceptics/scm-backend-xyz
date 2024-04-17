from django import template
from custom_registration.models import Seller
from transaction.models import Buyer
from invoice_generator.models import CollateralManager

register = template.Library()

@register.simple_tag
def seller_count():
    return Seller.objects.count()

@register.simple_tag
def buyer_count():
    return Buyer.objects.count()

@register.simple_tag
def collateral_manager_count():
    return CollateralManager.objects.count()
