# Expense Tracker API

A robust RESTful API built with Django and Django REST Framework for managing and analyzing personal or business financial expenses.

## Project Structure & Core Components

This project is organized into a modular Django application structure. The primary application logic lives inside the `expenses` directory.

- **`models.py` (Database Structure):** Defines the `Expense` model with fields for title, amount, category, description, and expense_date. It includes strict data integrity rules, such as `MinValueValidator` for amounts and a custom `validate_past_or_today` validator to ensure expenses cannot be logged with future dates.
- **`serializers.py` (Data Transformation):** Contains `ExpenseSerializer`, which acts as a bridge between the database and JSON output. It enforces a second layer of validation before any data touches the database (checking for empty titles, non-positive amounts, and future dates).
- **`views.py` (Business Logic & Controllers):** Utilizes `ModelViewSet` to automatically generate standard CRUD operations. It also integrates search, filtering, pagination, and a custom `@action` for calculating expense summaries using database aggregation.
- **`urls.py` (Routing):** Uses a `DefaultRouter` to automatically map the ViewSet actions to clean, predictable RESTful URL patterns.
- **`tests.py` (Quality Assurance):** A comprehensive test suite using `pytest` and `pytest-django`, utilizing isolated test databases, fixtures for reusable data, and `APIClient` to simulate endpoint interactions.

---

## API Endpoints Overview

The API is mounted at the `/expenses/` base route (assuming default router setup).

### 1. List and Create Expenses
**Endpoint:** `/expenses/`

* **GET** - List Expenses
  * Retrieves a paginated list of all expenses.
  * **Pagination:** Returns 10 items per page by default (customizable via `?page_size=`).
  * **Filtering:** Filter by category or date. Example: `/expenses/?category=Food`
  * **Searching:** Search through titles and descriptions. Example: `/expenses/?search=coffee`
  * **Ordering:** Order by amount, date, or creation time. Example: `/expenses/?ordering=-amount` (descending amount).
  
* **POST** - Create an Expense
  * Creates a new expense record.
  * **Payload Requirements:**
    * `title` (string, required, max 255 chars)
    * `amount` (decimal, required, must be > 0.01)
    * `category` (string, required, must match `CATEGORY_CHOICES`)
    * `expense_date` (date, required, format YYYY-MM-DD, cannot be in the future)
    * `description` (string, optional)

### 2. Retrieve, Update, and Delete
**Endpoint:** `/expenses/{id}/`

* **GET** - Retrieve a Specific Expense
  * Returns the full details of a single expense based on its integer ID.
* **PUT / PATCH** - Update an Expense
  * Modifies an existing expense. `PUT` requires the full payload, while `PATCH` allows partial updates (e.g., just updating the amount). All model and serializer validations still apply during updates.
* **DELETE** - Delete an Expense
  * Permanently removes the expense record from the database. Returns a `204 No Content` status on success.

### 3. Expense Summary
**Endpoint:** `/expenses/summary/`

* **GET** - Analytics Dashboard Data
  * A custom, non-CRUD endpoint that performs database-level aggregations (Sum, Count, Avg, Max, Min) across the entire `Expense` table.
  * **Response Format:**
    ```json
    {
      "total_expense": 1250.50,
      "total_entries": 45,
      "average_expense": 27.78,
      "highest_expense": 500.00,
      "lowest_expense": 1.50
    }
    ```
  * *Note:* If there are no expenses logged, the API gracefully handles it and returns `0` for all fields instead of throwing math errors (like dividing by zero).

---

## Testing

The project uses `pytest` for executing unit tests. Tests are located in `expenses/tests.py`.

**To run tests:**
```bash
# Make sure your virtual environment is active
source venv/bin/activate

# Run the test suite
pytest -v
```

The test suite thoroughly covers:
- **Creation/Retrieval/Update/Deletion:** Ensuring standard REST behaviors function as intended.
- **Validation Fallbacks:** Specifically feeding bad data (empty titles, negative amounts, future dates) to ensure the API safely rejects it with a `400 Bad Request`.
- **Summary Logic:** Ensuring the analytics endpoint calculates math accurately.
