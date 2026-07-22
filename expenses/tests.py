import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Expense

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def expense_data():
    return {
        'title': 'Test Coffee',
        'amount': '5.50',
        'category': 'Food',
        'expense_date': timezone.now().date(),
        'description': 'Morning coffee'
    }

@pytest.fixture
def expense(expense_data):
    return Expense.objects.create(**expense_data)

@pytest.mark.django_db
class TestExpenseAPI:
    """
    Test suite for the Expense API using pytest.
    """
    
    def test_create_expense(self, api_client, expense):
        url = reverse('expense-list')
        new_expense = {
            'title': 'New Book',
            'amount': '25.00',
            'category': 'Entertainment',
            'expense_date': timezone.now().date(),
        }
        response = api_client.post(url, new_expense, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Expense.objects.count() == 2

    def test_retrieve_expense(self, api_client, expense, expense_data):
        url = reverse('expense-detail', kwargs={'pk': expense.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == expense_data['title']

    def test_update_expense(self, api_client, expense, expense_data):
        url = reverse('expense-detail', kwargs={'pk': expense.pk})
        updated_data = expense_data.copy()
        updated_data['amount'] = '10.00'
        response = api_client.put(url, updated_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        expense.refresh_from_db()
        assert expense.amount == Decimal('10.00')

    def test_delete_expense(self, api_client, expense):
        url = reverse('expense-detail', kwargs={'pk': expense.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Expense.objects.count() == 0

    def test_validation_failure(self, api_client):
        url = reverse('expense-list')
        invalid_expense = {
            'title': '', # Invalid: empty
            'amount': '-5.00', # Invalid: negative
            'category': 'Food',
            'expense_date': (timezone.now() + timedelta(days=1)).date(), # Invalid: future
        }
        response = api_client.post(url, invalid_expense, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data
        assert 'amount' in response.data
        assert 'expense_date' in response.data

    def test_summary_endpoint(self, api_client, expense):
        Expense.objects.create(
            title='Train Ticket',
            amount='15.00',
            category='Transport',
            expense_date=timezone.now().date()
        )
        url = reverse('expense-summary')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_entries'] == 2
        assert response.data['total_expense'] == Decimal('20.50')

    def test_summary_endpoint_with_filters(self, api_client, expense):
        Expense.objects.create(
            title='Train Ticket',
            amount='15.00',
            category='Transport',
            expense_date=timezone.now().date()
        )
        # Filter by category
        url = f"{reverse('expense-summary')}?category=Food"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_entries'] == 1
        assert response.data['total_expense'] == Decimal('5.50')

        # Filter by search
        url = f"{reverse('expense-summary')}?search=Train"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_entries'] == 1
        assert response.data['total_expense'] == Decimal('15.00')

    def test_summary_endpoint_empty_db(self, api_client):
        Expense.objects.all().delete()
        url = reverse('expense-summary')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_entries'] == 0
        assert response.data['total_expense'] == Decimal('0.00')
        assert isinstance(response.data['total_expense'], Decimal)
        assert isinstance(response.data['average_expense'], Decimal)

