from django.contrib import admin
from django.urls import path, include  # Add re_path for compatibility
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
# from accounts.views import Profile, ProfileViewset
# from accounts import views
from transaction import views as trade_views  # Import views as trade_views

from transaction.views import (
    AbattoirPaymentToBreaderViewSet,
    BreaderViewSet,
     AbattoirViewSet, 
     BreaderViewSet,
      BreaderTradeViewSet,
       AbattoirPaymentToBreaderViewSet,
       BreaderCountView, UserSuppliedBreedsViewSet,
        BreaderTradeSingleUserViewSet,
        InventoryViewSet,
        BreaderTradeSingleSellerViewSet,
        BreaderTradeAllSingleSellerViewSet,
)
from invoice_generator import views as quotation_views
from inventory_management.views import InventoryBreedViewSet, InventoryBreedSalesViewSet, BreedCutViewSet, BreederTotalSerializer, BreederTotalViewSet, BreedCutTotalViewSet, BreederTotalSingleSellerViewSet
from slaughter_house.views import SlaughterhouseRecordViewSet
# from accounts.views import get_csrf_token
from mpesa_payments.views import MpesaPaymentView
from invoice_generator.views import (
    BuyerViewSet,
    InvoiceViewSet,
    InvoiceAllViewSet,
    LetterOfCreditViewSet,
    LetterOfCreditAllViewSet,
    download_invoice_document,
    download_lc_document,
    PurchaseOrderViewSet,
    LetterOfCreditSellerToTraderViewSet,
    ProformaInvoiceFromTraderToSellerViewSet,
    QuotationViewSet,
    QuotationAllViewSet,
    DocumentToSellerViewSet,
    BuyerAllViewSet
)
from slaughter_house.views import SupplyVsDemandStatisticsViewSet, compare_weight_loss
from logistics.views import LogisticsStatusViewSet, OrderViewSet, ShipmentProgressViewSet, ArrivedOrderViewSet, LogisticsStatusAllViewSet, PackageInfoViewset, CollateralManagerViewSet, ControlCenterViewSet

from dj_rest_auth.registration.views import (
    ResendEmailVerificationView,
    VerifyEmailView,
)
from dj_rest_auth.views import (
    PasswordResetView,
    LoginView,
    UserDetailsView,
    LogoutView,
)
from allauth.account.views import (
    LoginView as AllAuthLoginView,
    LogoutView as AllAuthLogoutView,
    PasswordResetDoneView as AllAuthPasswordResetDoneView,
)

# from accounts.views import (
#     Profile,
#     ProfileViewset,
#     # email_confirm_redirect,
#     # password_reset_confirm_redirect,
#     GetUserRole,
# )

from custom_registration import views

from custom_registration.views import (
    CustomTokenObtainPairView,
    CustomUserLoginViewSet,
    CustomUserRegistrationViewSet,
    CustomLogoutViewSet,
    CustomTokenRefreshView,
    UserProfileView,
    UserProfileViewSet,
    GetUserRole,
    UserProfilesListView,
    RoleListView,
    PaymentViewSet, CustomerServiceViewSet,
    PasswordResetRequestView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetConfirmationView,
    CustomPasswordResetCompleteView,
    CustomPasswordResetDoneView,
    SellerViewSet,
    SellerAllViewSet,
)

from custom_registration import views

# Payments
from payments.views import make_payment

router = DefaultRouter()
# app_name = 'payments'
app_name = 'invoice_generator'

buyer_list = BuyerViewSet.as_view({'get': 'list'})
buyer_detail = BuyerViewSet.as_view({'get': 'retrieve'})

invoice_list = InvoiceViewSet.as_view({'get': 'list', 'post': 'create'})
invoice_detail = InvoiceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

lc_list = LetterOfCreditViewSet.as_view({'get': 'list', 'post': 'create'})
lc_detail = LetterOfCreditViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

# Breeders
router.register(r'traders', BreaderViewSet)

# supply vs demand
router.register(r'supply-vs-demand', SupplyVsDemandStatisticsViewSet, basename='supply-vs-demand')

# Purchase order and Lc Local. Profoma invoice
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-orders')
router.register(r'letters-of-credit-to-local-traders', LetterOfCreditSellerToTraderViewSet, basename='letters-of-credit-to-local-traders')
router.register(r'all-lcs', LetterOfCreditAllViewSet, basename='all-lcs')

router.register(r'profoma-invoice-to-local-sellers', ProformaInvoiceFromTraderToSellerViewSet, basename='profoma-invoice-to-local-sellers')

    # router.register(r'profile', ProfileViewset)
router.register(r'documents-to-seller', DocumentToSellerViewSet)

# breed sales from transaction
router.register(r'inventory-breed-sales', InventoryBreedSalesViewSet)

router.register(r'inventory-breed-name', InventoryBreedViewSet)

# Ready -breed and trade
router.register(r'breader-trade', BreaderTradeViewSet)

router.register(r'breader-trade-to-seller', BreaderTradeAllSingleSellerViewSet, basename='breader_trade_to_seller')
router.register(r'breader-trade-seller', BreaderTradeSingleSellerViewSet, basename='breader_trade_seller')

router.register(r'breader-trade-id', BreaderTradeSingleUserViewSet)

# router.register(r'all-breeder_totals', BreederTotalViewSet, basename='all-cut_totals')
router.register(r'breeder_totals', BreederTotalSingleSellerViewSet, basename='cut_totals')
router.register(r'part_totals_count', BreedCutTotalViewSet, basename='breeder_totals')

# breeder single user
router.register(r'user-supplied-breeds', UserSuppliedBreedsViewSet, basename='user-supplied-breeds')

# Inventory management
router.register(r'abattoirs', AbattoirViewSet)
router.register(r'breaders', BreaderViewSet)
router.register(r'breed-cut', BreedCutViewSet)
router.register(r'slaughtered-list', SlaughterhouseRecordViewSet)
router.register(r'abattoir-payments', AbattoirPaymentToBreaderViewSet)
router.register(r'breader-info-trade', BreaderTradeViewSet, basename='breader-trade')
router.register(r'inventory', InventoryViewSet, basename='inventory')

# 
router.register(r'abattoir-payments-to-breeder', AbattoirPaymentToBreaderViewSet, basename='abattoir-payments-to-breeder')

router.register(r'abattoir-payments-to-breeders/search-payment-by-code', AbattoirPaymentToBreaderViewSet, basename='search-payment-by-code')

# custom registration

router.register(r'login', CustomUserLoginViewSet, basename='login')
router.register(r'register', CustomUserRegistrationViewSet, basename='register')
router.register(r'logout', CustomLogoutViewSet, basename='logout')
router.register(r'profiles', UserProfileViewSet, basename='profile')

# sellers
router.register(r'sellers', SellerViewSet, basename='sellers')
router.register(r'all-sellers', SellerAllViewSet, basename='sellers')

# Buyer
router.register(r'register-buyer', CustomUserRegistrationViewSet, basename='register-buyer')
router.register(r'send-quotation', QuotationViewSet, basename='send-quotation')
router.register(r'quotations', QuotationAllViewSet, basename='quotations')

# Payments

# router.register(r'payments-to-breeder', PaymentViewSet, basename='payment_to_breeder')
router.register(r'payments-to-breeder', AbattoirPaymentToBreaderViewSet, basename='payment_to_breeder')

# Customer service
router.register(r'customer-service', CustomerServiceViewSet, basename='customer-service')

# Logistics management
router.register(r'package-info', PackageInfoViewset, basename='package-info')

router.register(r'logistics-status', LogisticsStatusViewSet, basename='logistics')
router.register(r'all-logistics-statuses', LogisticsStatusAllViewSet, basename='all-logistics-statuses')

router.register(r'order', OrderViewSet, basename='order')
router.register(r'shipment-progress', ShipmentProgressViewSet, basename='shipment-progress')
router.register(r'arrived-order', ArrivedOrderViewSet, basename='arrived-order')

# Purchase order

# router.register(r'products', ProductViewSet, basename='product')
# router.register(r'items', ItemViewSet, basename='item')
# router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')



# Invoice

# Create a router and register our viewsets with it.
router.register(r'generate-invoice', InvoiceViewSet)
router.register(r'invoices', InvoiceAllViewSet)

router.register(r'buyers', BuyerViewSet)
router.register(r'all-buyers', BuyerAllViewSet)

# Control centers

router.register(r'control-centers', ControlCenterViewSet)
router.register(r'collateral-managers', CollateralManagerViewSet, basename='collateral-manager')

schema_view = get_schema_view(
   openapi.Info(
      title="SCM APIs",
      default_version='v1',
      description="Test description",
      contact=openapi.Contact(email="owillypascal@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),

   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('intellima_administration/', admin.site.urls),

    # new purchase order

    # custom registration

    path('auth/token/', CustomTokenObtainPairView.as_view(), name='auth-token'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/user/', UserProfileView.as_view(), name='user-profile'),  # Use .as_view() for class-based views
    path('get-user-role/', GetUserRole.as_view(), name='get_user_role'),
    path('auth/all-profiles/', UserProfilesListView.as_view(), name='get_user_role'),
    path('api/roles/', RoleListView.as_view(), name='role-list'),

    path('api/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('api/password-reset/confirm/<str:uidb64>/<str:token>/', CustomPasswordResetConfirmationView.as_view(), name='password-reset-confirm'),

    path('api/', include(router.urls)),
    path('api/breader-count/', BreaderCountView.as_view(), name='breader-count'),
    # path('api/total_breeds_supplied/', total_breeds_supplied, name='total_breeds_supplied'),
    
    # path('api/supply-vs-demand/', supply_vs_demand_statistics, name='supply_vs_demand_statistics'),
    path('api/compare-weight-loss-after-slaughter/', compare_weight_loss, name='compare-weight-loss-after-slaughter'),

    # Equity bank Payments
    # path('make_payment/<int:breeder_trade_id>/', make_payment, name='make_payment'),
    path('api/make-payment/<int:breeder_trade_id>/', make_payment, name='make_epayment'),
   # paymens list
    path('api/payments-list/', PaymentViewSet.as_view({'get': 'list_payments'}), name='list_payments'),
  
    # Search breeder by code 
    path('api/abattoir-payments-to-breeder/search-payment-by-code/', AbattoirPaymentToBreaderViewSet.as_view({'get': 'search_payment_by_code'}), name='search-payment-by-code'),

    # logistics
    path('api/logistics-status/<int:invoice_id>/', LogisticsStatusViewSet.as_view({'get': 'retrieve'}), name='logistics-status-detail'),

    # Notify buyer
    # path('api/notify_buyer/<int:purchase_order_id>/', NotifyBuyerView.as_view(), name='notify_buyer'),

    #  create purchase order
    # path('api/create-purchase-order/', create_purchase_order, name='create_purchase_order'),

    # LC
     # Download LC AND Invoice
    path('api/buyers/', buyer_list, name='buyer-list'),
    path('api/buyers/<int:pk>/', buyer_detail, name='buyer-detail'),
    
    path('api/invoices/', invoice_list, name='invoice-list'),
    path('api/invoices/<int:pk>/', invoice_detail, name='invoice-detail'),
    path('api/invoices/<int:invoice_id>/download/', download_invoice_document, name='download-invoice'),

    path('api/letter_of_credits/', lc_list, name='lc-list'),
    path('api/letter_of_credits/<int:pk>/', lc_detail, name='lc-detail'),
    path('api/letter_of_credits/<int:lc_id>/download/', download_lc_document, name='download-lc'),
    
    # customer service viewset

    path('mpesa-payment/', MpesaPaymentView.as_view(), name = 'mpesa payments'),
    # path('api/csrf_token/', get_csrf_token, name='csrf_token'),
    # path('accounts/', include('allauth.account.urls')),  # This includes allauth's registration views
    # path('auth/', include('accounts.urls')),
    # path('registration/', include('custom_registration.urls')),
    path('drf/', include('rest_framework.urls', namespace='rest_framework')),
    path('swagger/<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('intellima_base_apis', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # TEMPLATES

    # auth
    path('', views.home, name='home'),  # Ensure the URL pattern ends with a trailing slash
    path('register/', views.register_user, name='register'),
    path('login/', views.login_view, name='login'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),  # Add this line
    path('logout/', views.logout_view, name='custom_logout'),

    path('register/buyer/', views.register_buyer, name='buyer_register'),
    path('register/breeder/', views.register_breeder, name='breeder_register'),
    path('register/seller/', views.register_seller, name='seller_register'),
    path('register/bank/', views.register_bank, name='bank_register'),
    path('register/collateral-manager/', views.register_collateral_manager, name='collateral_manager_register'),
    path('unauthorized/', views.unauthorized, name='unauthorized'),

    # dashboards
    path('dashboard/seller/', views.seller_dashboard, name='seller_dashboard'),
    path('dashboard/breeder/', views.breeder_dashboard, name='breeder_dashboard'),
    path('dashboard/buyer/', views.buyer_dashboard, name='buyer_dashboard'),
    path('dashboard/stock-shift/', views.stock_shift_dashboard, name='stock_shift_dashboard'),
    path('dashboard/bank/', views.bank_dashboard, name='bank_dashboard'),
    path('dashboard/control-centers/', views.control_centers_dashboard, name='control_centers_dashboard'),
    path('dashboard/export-management/', views.export_management_dashboard, name='export_management'),

    # Transaction urls
    path('trade/create_breader_trade/', trade_views.create_breader_trade, name='create_breader_trade'),
    path('trade/success/', trade_views.success_view, name='success_url'),
    path('trade/supply-history/', trade_views.supply_history, name='supply_history'),
    path('trade/seller_supply-history/', trade_views.seller_breeder_trade, name='seller_supply_history'),

    # Quotatopn
    path('quotation/list/', quotation_views.quotation_list, name='quotation_list'),
    path('quotation/create/', quotation_views.create_quotation, name='create_quotation'),
]

# Only add this when we are in debug mode.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
