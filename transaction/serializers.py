# serializers.py
from rest_framework import serializers
from transaction.models import Abattoir, Breader, BreaderTrade, AbattoirPaymentToBreader, Inventory
from custom_registration.models import CustomUser

class AbattoirSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abattoir
        fields = '__all__'

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['community', 'market', 'first_name', 'last_name']

class BreaderSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Breader
        fields = '__all__'

    
class BreaderTradeSerializer(serializers.ModelSerializer):
    breeder_first_name = serializers.CharField(source='breeder.first_name', read_only=True)
    breeder_last_name = serializers.CharField(source='breeder.last_name', read_only=True)
    breeder_market = serializers.CharField(source='breeder.market', read_only=True)
    breeder_community = serializers.CharField(source='breeder.community', read_only=True)
    breeder_head_of_family = serializers.CharField(source='breeder.head_of_family', read_only=True)

    email = serializers.CharField(source='get_breeder_email', read_only=True, allow_null=True)
    phone_number = serializers.CharField(source='get_breeder_phone_number', read_only=True, allow_null=True)
    id_number = serializers.CharField(source='get_breeder_id_number', read_only=True, allow_null=True)
    bank_account_number = serializers.CharField(source='get_breeder_bank_account_number', read_only=True, allow_null=True)

    class Meta:
        model = BreaderTrade
        fields = ['id', 'email', 'phone_number', 'id_number', 'bank_account_number', 'breeder', 'seller', 'control_center', 'transaction_date', 'breed', 'breeds_supplied', 'goat_weight', 'vaccinated', 'created_at', 'price', 'reference', 'breeder_first_name', 'breeder_last_name', 'breeder_market', 'breeder_community', 'breeder_head_of_family']

class InventorySerializer(serializers.ModelSerializer):
    trade = BreaderTradeSerializer(many=True)

    class Meta:
        model = Inventory
        fields = '__all__'

class AbattoirPaymentToBreaderSerializer(serializers.ModelSerializer):
    breeder_trade = BreaderTradeSerializer()

    class Meta:
        model = AbattoirPaymentToBreader
        fields = '__all__'

    def create(self, validated_data):
        # Extract the 'breeder_trade' data from the validated data
        breeder_trade_data = validated_data.pop('breeder_trade')

        # Retrieve an existing BreaderTrade instance based on some criteria (e.g., breeder_trade_id)
        breeder_trade_instance = BreaderTrade.objects.get(id=breeder_trade_data.get('id'))

        # Set the 'breeder_trade' field with the retrieved BreaderTrade instance
        validated_data['breeder_trade'] = breeder_trade_instance

        # Call the superclass create method with the modified data
        instance = super().create(validated_data)

        print("Created Instance ID:", instance.payments_id)

        return instance



