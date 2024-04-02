from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from .models import InventoryBreed, InventoryBreedSales, BreedCut
from .serializers import InventoryBreedSerializer, InventoryBreedSalesSerializer, BreedCutSerializer, BreederTotalSerializer, BreedCutTotalSerializer
from transaction.models import BreaderTrade
from slaughter_house.models import SlaughterhouseRecord
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from custom_registration.models import CustomUser

from logistics.models import ControlCenter
from logistics.serializers import ControlCenterTotalSerializer

class InventoryBreedViewSet(viewsets.ModelViewSet):
    queryset = InventoryBreed.objects.all()
    serializer_class = InventoryBreedSerializer

class BreedCutViewSet(viewsets.ModelViewSet):
    queryset = BreedCut.objects.all()
    serializer_class = BreedCutSerializer

class BreedCutTotalViewSet(viewsets.ViewSet):

    def list(self, request):
        try:
            # Get the currently authenticated user
            user = request.user

            # Initialize user_control_centers as an empty queryset
            user_control_centers = ControlCenter.objects.none()

            # Get control centers associated with the user
            if user.role == CustomUser.SELLER:
                # Assuming the user is a seller
                user_control_centers = ControlCenter.objects.filter(seller=user)

            # Calculate total breed supply from BreaderTrade for control centers associated with the user
            breeder_totals = (
                BreaderTrade.objects
                .filter(control_center__in=user_control_centers)
                .values('control_center__id', 'breed')
                .annotate(total_breed_supply=Sum('breeds_supplied'))
            )

            # Calculate total slaughtered from SlaughterhouseRecord for all breeds
            slaughtered_quantities = (
                SlaughterhouseRecord.objects
                .values('breed')
                .annotate(total_slaughtered=Sum('quantity'))
            )

            # Create a dictionary to hold the total breed supply per breed and control center
            total_dict = {}

            # Calculate total breed supply per control center and breed
            for total in breeder_totals:
                control_center_id = total['control_center__id']
                breed = total['breed']
                total_dict.setdefault((control_center_id, breed), {'control_center__id': control_center_id, 'breed': breed, 'total_breed_supply': 0})
                total_dict[(control_center_id, breed)]['total_breed_supply'] += total['total_breed_supply']

            # Subtract slaughtered quantities from the total breed supply per control center and breed
            for slaughtered_quantity in slaughtered_quantities:
                breed = slaughtered_quantity['breed']
                for key, value in total_dict.items():
                    control_center_id, breed_in_dict = key
                    if breed_in_dict == breed:
                        total_dict[key]['total_breed_supply'] -= slaughtered_quantity['total_slaughtered']
                        # Ensure the total breed supply doesn't go negative
                        if total_dict[key]['total_breed_supply'] < 0:
                            total_dict[key]['total_breed_supply'] = 0  # Set to 0 if negative

            # Convert the dictionary values to a list
            breeder_totals = list(total_dict.values())

            return Response(breeder_totals)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BreederCutTotalViewSet(viewsets.ViewSet):
    def list(self, request):
        # Calculate total breed cuts from BreadCut
        breed_cut_totals = (
            BreadCut.objects
            .values('bread__id', 'part_name')
            .annotate(total_breed_part=Sum('quantity'))
        )

        # Calculate total slaughtered from SlaughterhouseRecord
        slaughtered_quantities = (
            SlaughterhouseRecord.objects
            .values('part_name')
            .annotate(total_slaughtered=Sum('quantity'))
        )

        # Combine both results into a dictionary for easy access
        total_dict = {}
        for total in breed_cut_totals:
            bread_id = total['bread__id']
            breed = total['part_name']
            total_dict.setdefault(breed, {'bread__id': bread_id, 'total_breed_part': 0, 'breed': breed})
            total_dict[breed]['total_breed_part'] += total['total_breed_part']

        for slaughtered_quantity in slaughtered_quantities:
            part_name = slaughtered_quantity['part_name']
            total_dict.setdefault(part_name, {'bread__id': None, 'total_breed_part': 0, 'part_name': part_name})
            
            # Check if breed exists in total_dict before subtracting
            if part_name in total_dict:
                # Validate before subtracting
                remaining_breed_part = total_dict[part_name]['total_breed_part'] - slaughtered_quantity['total_slaughtered']
                if remaining_breed_part < 0:
                    raise ValueError(f"Cannot slaughter {slaughtered_quantity['total_slaughtered']} of breed {part_name}. Insufficient breed parts.")
                total_dict[part_name]['total_breed_part'] = remaining_breed_part

        # Convert the dictionary values to a list
        breed_part_totals = list(total_dict.values())
        
        # Ensure all entries have 'breed_part' key
        for entry in breed_part_totals:
            entry['breed_part'] = entry.get('breed_part', None)
        
        serializer = BreederTotalSerializer(breed_part_totals, many=True)
        return Response(serializer.data)

class InventoryBreedSalesViewSet(viewsets.ModelViewSet):
    queryset = InventoryBreedSales.objects.all()
    serializer_class = InventoryBreedSalesSerializer

class BreederTotalViewSet(viewsets.ViewSet):

    def list(self, request):
        try:
            # Calculate total breed supply from BreaderTrade
            breeder_totals = (
                BreaderTrade.objects
                .values('control_center__id', 'breed')
                .annotate(total_breed_supply=Sum('breeds_supplied'))
            )

            # Calculate total slaughtered from SlaughterhouseRecord
            slaughtered_quantities = (
                SlaughterhouseRecord.objects
                .values('breed')
                .annotate(total_slaughtered=Sum('quantity'))
            )

            # Create a dictionary to hold the total breed supply per breed and control center
            total_dict = {}

            # Calculate total breed supply per control center and breed
            for total in breeder_totals:
                control_center_id = total['control_center__id']
                breed = total['breed']
                total_dict.setdefault((control_center_id, breed), {'breader__id': control_center_id, 'breed': breed, 'total_breed_supply': 0})
                total_dict[(control_center_id, breed)]['total_breed_supply'] += total['total_breed_supply']

            # Subtract slaughtered quantities from the total breed supply per control center and breed
            for slaughtered_quantity in slaughtered_quantities:
                breed = slaughtered_quantity['breed']
                for key, value in total_dict.items():
                    control_center_id, breed_in_dict = key
                    if breed_in_dict == breed:
                        total_dict[key]['total_breed_supply'] -= slaughtered_quantity['total_slaughtered']
                        # Ensure the total breed supply doesn't go negative
                        if total_dict[key]['total_breed_supply'] < 0:
                            total_dict[key]['total_breed_supply'] = 0  # Set to 0 if negative

            # Convert the dictionary values to a list
            breeder_totals = list(total_dict.values())

            serializer = BreederTotalSerializer(breeder_totals, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BreederTotalSingleSellerViewSet(viewsets.ViewSet):

    def list(self, request):
        try:
            # Get the ID of the currently authenticated user (assuming it's the seller)
            seller_id = request.user.id

            # Get control centers associated with the seller
            seller_control_centers = ControlCenter.objects.filter(breadertrade__seller_id=seller_id).distinct()

            # Aggregate total breeds supplied from BreaderTrade for control centers associated with the seller
            control_center_totals = (
                BreaderTrade.objects
                .filter(control_center__in=seller_control_centers)  # Filter BreaderTrades by control centers associated with the seller
                .values('control_center__id', 'breed')
                .annotate(
                    total_breed_supply=Sum('breeds_supplied'),  # Calculate total breed supply from related BreaderTrades
                    total_slaughtered=Coalesce(Sum('control_center__slaughterhouserecord__quantity'), Value(0))  # Calculate total slaughtered from related SlaughterhouseRecords
                )
            )

            # Deduct slaughtered quantity from total breed supply for each control center
            for control_center_total in control_center_totals:
                total_breed_supply = control_center_total['total_breed_supply']
                total_slaughtered = control_center_total['total_slaughtered']
                control_center_total['net_breed_supply'] = total_breed_supply - total_slaughtered if total_slaughtered is not None else total_breed_supply
                # Ensure the net breed supply doesn't go negative
                if control_center_total['net_breed_supply'] < 0:
                    control_center_total['net_breed_supply'] = 0

            # Sort the control_center_totals list based on net_breed_supply in descending order
            control_center_totals = sorted(control_center_totals, key=lambda x: x['net_breed_supply'], reverse=True)

            return Response(control_center_totals)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)