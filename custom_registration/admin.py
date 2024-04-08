from django.contrib import admin
from custom_registration.models import CustomUser,UserProfile, Status, Payment, CustomerService, BankTeller, Seller

admin.site.register(CustomUser)
# admin.site.register(Bank)
# admin.site.register(BankBranch)
admin.site.register(Status)
admin.site.register(Payment)
admin.site.register(CustomerService)
admin.site.register(BankTeller)
admin.site.register(Seller)
admin.site.register(UserProfile)




