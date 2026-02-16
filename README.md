
# InventoryAI Flask Application

This is a prototype inventory management application built with Flask.

## Prerequisites

- Python 3.x
- `pip`

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  Run the application:
    ```bash
    python app.py
    ```
    Or if you have the `py` launcher:
    ```bash
    py app.py
    ```

2.  Open your browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Routes

-   `/` - Login Page
-   `/dashboard` - Main Dashboard
-   `/forecast/<sku_id>` - Forecasting Page
-   `/generate-pr` - Purchase Request Generator
