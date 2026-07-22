from decimal import Decimal
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Avg, Max, Min
from .models import Expense
from .serializers import ExpenseSerializer


class ExpensePagination(PageNumberPagination):
    """
    Custom pagination class for the ExpenseViewSet.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations and custom endpoints for Expenses.
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    pagination_class = ExpensePagination
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'expense_date']
    search_fields = ['title', 'description']
    ordering_fields = ['amount', 'expense_date', 'created_at']
    ordering = ['-expense_date']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Custom endpoint to get a summary of all expenses.
        """
        queryset = self.filter_queryset(self.get_queryset())
        summary_data = queryset.aggregate(
            total_expense=Sum('amount'),
            total_entries=Count('id'),
            average_expense=Avg('amount'),
            highest_expense=Max('amount'),
            lowest_expense=Min('amount')
        )
        
        if summary_data['total_entries'] == 0:
            summary_data = {
                'total_expense': Decimal('0.00'),
                'total_entries': 0,
                'average_expense': Decimal('0.00'),
                'highest_expense': Decimal('0.00'),
                'lowest_expense': Decimal('0.00')
            }
        else:
            summary_data['total_expense'] = round(summary_data['total_expense'], 2) if summary_data['total_expense'] is not None else Decimal('0.00')
            summary_data['average_expense'] = round(summary_data['average_expense'], 2) if summary_data['average_expense'] is not None else Decimal('0.00')
            summary_data['highest_expense'] = round(summary_data['highest_expense'], 2) if summary_data['highest_expense'] is not None else Decimal('0.00')
            summary_data['lowest_expense'] = round(summary_data['lowest_expense'], 2) if summary_data['lowest_expense'] is not None else Decimal('0.00')

        return Response(summary_data)
