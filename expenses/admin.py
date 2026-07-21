from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Expense model.
    """
    list_display = ('title', 'amount', 'category', 'expense_date', 'created_at')
    list_filter = ('category', 'expense_date')
    search_fields = ('title', 'description')
    ordering = ('-expense_date',)
