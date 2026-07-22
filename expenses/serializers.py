from rest_framework import serializers
from .models import Expense
from django.utils import timezone

class ExpenseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Expense model. Handles data transformation and validation.
    """
    class Meta:
        model = Expense
        fields = '__all__'
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_expense_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Expense date cannot be in the future.")
        return value


class DateRangeSerializer(serializers.Serializer):
    """
    Serializer to validate date range query parameters.
    """
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("start_date cannot be after end_date.")
        return data

