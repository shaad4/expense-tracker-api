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

    def test_date_range_endpoint_success(self, api_client, expense):
        # Create expenses outside and inside the range
        today = timezone.now().date()
        Expense.objects.create(
            title='Yesterday Expense',
            amount='12.50',
            category='Shopping',
            expense_date=today - timedelta(days=1)
        )
        Expense.objects.create(
            title='Tomorrow Expense',
            amount='18.00',
            category='Shopping',
            expense_date=today + timedelta(days=1) # wait, future is blocked by model validation but test_db might bypass or raise error, wait! Let's check models.py: validate_past_or_today. Oh! Expense cannot be in the future. Let's make it past.
        )
        # Let's create:
        # 1. 5 days ago
        # 2. 2 days ago (which is start_date)
        # 3. Today (which is end_date)
        # range: 3 days ago to today.
        Expense.objects.all().delete()
        
        e1 = Expense.objects.create(
            title='5 days ago',
            amount='10.00',
            category='Shopping',
            expense_date=today - timedelta(days=5)
        )
        e2 = Expense.objects.create(
            title='3 days ago',
            amount='20.00',
            category='Food',
            expense_date=today - timedelta(days=3)
        )
        e3 = Expense.objects.create(
            title='1 day ago',
            amount='30.00',
            category='Food',
            expense_date=today - timedelta(days=1)
        )
        
        url = reverse('expense-date-range')
        response = api_client.get(url, {
            'start_date': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
            'end_date': today.strftime('%Y-%m-%d')
        })
        assert response.status_code == status.HTTP_200_OK
        # Since pagination is active, let's check results key or list
        # Wait, how is pagination output structured? ExpensePagination has page_size = 10.
        # Since we have 2 records in range (e2 and e3), they will fit in page 1.
        # Let's assert 'results' is in response.data or it's a list.
        # Let's check if the paginated structure has results. Yes, DRF's standard PageNumberPagination uses 'results'.
        assert 'results' in response.data
        results = response.data['results']
        assert len(results) == 2
        titles = [r['title'] for r in results]
        assert '3 days ago' in titles
        assert '1 day ago' in titles
        assert '5 days ago' not in titles

    def test_date_range_endpoint_validation_errors(self, api_client):
        url = reverse('expense-date-range')
        today = timezone.now().date()

        # Missing params
        response = api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # start_date > end_date
        response = api_client.get(url, {
            'start_date': today.strftime('%Y-%m-%d'),
            'end_date': (today - timedelta(days=1)).strftime('%Y-%m-%d')
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Invalid date format
        response = api_client.get(url, {
            'start_date': 'invalid-date',
            'end_date': today.strftime('%Y-%m-%d')
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


