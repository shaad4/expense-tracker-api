from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

def validate_past_or_today(value):
    """
    Validator to ensure the expense date is not in the future.
    """
    if value > timezone.now().date():
        raise ValidationError('Expense date cannot be in the future.')

class Expense(models.Model):
    """
    Model representing a financial expense.
    """
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Shopping', 'Shopping'),
        ('Bills', 'Bills'),
        ('Entertainment', 'Entertainment'),
        ('Health', 'Health'),
        ('Other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    expense_date = models.DateField(validators=[validate_past_or_today])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.title} - {self.amount}"
