
# InventoryAI Flask Application

This is a prototype inventory management application built with Flask.

## Prerequisites

- Python 3.x
- `pip` or `uv` (recommended)

## Setup with uv (Recommended)

1.  **Install uv** (if not already installed):
    ```bash
    pip install uv
    ```
    Or check [uv documentation](https://docs.astral.sh/uv/getting-started/installation/) for other installation methods.

2.  **Create a virtual environment:**
    ```bash
    uv venv
    ```

3.  **Activate the virtual environment:**
    *   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```
    *   **Windows:**
        ```powershell
        .venv\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

## Setup with pip (Standard)

1.  Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    # Linux/macOS
    source venv/bin/activate
    # Windows
    venv\Scripts\activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Database Setup

Before running the application, you need to initialize the database and seed it with sample data:

```bash
python seed_data.py
```
This will create `inventory.db` and populate it with Users, Products, Inventory, and Forecast data.

## Running the Application

1.  Run the application:
    ```bash
    python app.py
    ```

2.  Open your browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

3.  **Login Credentials:**
    *   **Admin/Procurement:** `admin@inventory.ai` / `admin123`
    *   **Sales:** `sales@inventory.ai` / `sales123`

## Routes

-   `/` - Login Page
-   `/dashboard` - Main Dashboard
-   `/forecast/<sku_id>` - Forecasting Page
-   `/generate-pr` - Purchase Request Generator
