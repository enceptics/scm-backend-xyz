from rest_framework import serializers
from .models import Invoice, Buyer,LetterOfCredit, LetterOfCreditSellerToTrader, PurchaseOrder, ProformaInvoiceFromTraderToSeller, Quotation, DocumentToSeller
from custom_registration.models import CustomUser  
from custom_registration.serializers import SellerSerializer
from logistics.serializers import LogisticsStatusSerializer, LogisticsStatus


# Local Buyers and sellers

class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

class LetterOfCreditSellerToTraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterOfCreditSellerToTrader
        fields = '__all__'

class ProformaInvoiceFromTraderToSellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInvoiceFromTraderToSeller
        fields = '__all__'

class BuyerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name')
    username = serializers.CharField(source='get_user_name')
    email = serializers.CharField(source='get_user_email')
    address = serializers.CharField(source='get_user_address')
    country = serializers.CharField(source='get_user_country')
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Buyer
        fields = ['id', 'buyer', 'created_at', 'full_name', 'username', 'email', 'address', 'country', 'formatted_created_at']

    def get_formatted_created_at(self, obj):
        return obj.created_at.strftime('%B %d, %Y %I:%M %p')


class InvoiceSerializer(serializers.ModelSerializer):
    buyer_full_name = serializers.SerializerMethodField()
    buyer_user_name = serializers.SerializerMethodField()
    buyer_user_email = serializers.SerializerMethodField()
    buyer_user_country = serializers.SerializerMethodField()
    buyer_user_address = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = '__all__'

    def create(self, validated_data):
        return super().create(validated_data)

    def get_buyer_full_name(self, obj):
        if obj.buyer:
            return obj.buyer.get_full_name()
        return "Unknown"

    def get_buyer_user_name(self, obj):
        if obj.buyer:
            return obj.buyer.get_user_name()
        return "Unknown"

    def get_buyer_user_email(self, obj):
        if obj.buyer:
            return obj.buyer.get_user_email()
        return "Unknown"

    def get_buyer_user_country(self, obj):
        if obj.buyer:
            return obj.buyer.get_user_country()
        return "Unknown"

    def get_buyer_user_address(self, obj):
        if obj.buyer:
            return obj.buyer.get_user_address()
        return "Unknown"

class DocumentToSellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentToSeller
        fields = ['id', 'seller', 'message', 'uploaded_at']


class LetterOfCreditSerializer(serializers.ModelSerializer):
    buyer_full_name = serializers.CharField(source='get_buyer_full_name', read_only=True)
    seller_full_name = serializers.CharField(source='get_seller_full_name', read_only=True)

    class Meta:
        model = LetterOfCredit
        fields = ['id', 'status', 'buyer', 'buyer_full_name', 'seller_full_name', 'seller', 'issue_date', 'lc_document']

class LogisticsStatusSerializer(serializers.ModelSerializer):
    invoice = InvoiceSerializer()  

    class Meta:
        model = LogisticsStatus
        fields = ['id', 'status', 'timestamp', 'invoice']

class QuotationSerializer(serializers.ModelSerializer):
    letter_of_credit = LetterOfCreditSerializer(allow_null=True, required=False)
    buyer_full_name = serializers.CharField(source='get_buyer_full_name', allow_null=True, required=False)
    seller_full_name = serializers.CharField(source='get_seller_full_name', allow_null=True, required=False)
    buyer_email = serializers.CharField(source='get_buyer_email', allow_null=True, required=False)
    seller_email = serializers.CharField(source='get_seller_email', allow_null=True, required=False)
    buyer_address = serializers.CharField(source='get_buyer_address', allow_null=True, required=False)
    buyer_country = serializers.CharField(source='get_buyer_country', allow_null=True, required=False)
    seller_county = serializers.CharField(source='get_seller_county', allow_null=True, required=False)
    seller_address = serializers.CharField(source='get_seller_address', allow_null=True, required=False)

    class Meta:
        model = Quotation
        fields = ['id', 'seller','seller_county', 'buyer_country','seller_email','buyer_email','buyer_address','seller_address', 'buyer', 'product', 'confirm', 'quantity', 'delivery_time', 'unit_price', 'market', 'message', 'status', 'created_at', 'letter_of_credit', 'buyer_full_name', 'seller_full_name']
