# ChinHin Forecasting Pro API Documentation

## Overview
This document provides a comprehensive reference for the API layer of the **ChinHin Forecasting Pro** application. It maps out all backend routes provided by the Flask application (`app.py`), the expected request payloads and parameters, the JSON responses, and the specific user roles and permissions required to access each endpoint.

## Roles & Permissions
The application implements Role-Based Access Control (RBAC) via the `@role_required` and `@login_required` decorators in the Flask backend.

* **Admin**: Unrestricted access to system administration, user management, order confirmation, and warehouse operations.
* **Manager**: Access to overview statistics, adding products/vendors, confirming orders, assigning user locations, and viewing workspace users.
* **Warehouse**: Access to warehouse operations, generating purchase requests (PRs), and receiving orders.
* **Sales**: Access to sales quotations, modifying sale statuses, generating invoices, and viewing the sales dashboard.
* **Procurement**: (Assumed based on RBAC logic context) General access to the system, but specific destructive/creation routes may be limited compared to Manager/Admin.

*Note: All endpoints (except `/api/login` and `/api/client-logs`) require the user to be authenticated via a session cookie (established via `/api/login`).*

---

## API Reference

### Authentication & General

#### `POST /api/login`
- **Purpose**: Authenticates a user and establishes a session.
- **Required Role**: None (Public)
- **Request Payload**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "role": "Admin", "username": "admin", "email": "admin@example.com", "user_id": 1}`
  - **Error (401)**: `{"success": false, "message": "Invalid credentials"}`

#### `POST /api/logout`
- **Purpose**: Clears the current user's session.
- **Required Role**: Any Authenticated User
- **Request Payload**: None
- **Response Format**:
  - **Success (200)**: `{"success": true}`

#### `GET /api/check-auth`
- **Purpose**: Checks if the current session is valid and returns user info.
- **Required Role**: None (Returns 401 if unauthenticated)
- **Request Payload**: None
- **Response Format**:
  - **Success (200)**: `{"authenticated": true, "role": "Admin", "username": "admin"}`
  - **Error (401)**: `{"authenticated": false}`

#### `POST /api/client-logs`
- **Purpose**: Receives client-side frontend errors and logs them in the backend.
- **Required Role**: None (Public/Authenticated)
- **Request Payload**:
  ```json
  {
    "level": "error",
    "message": "Error description",
    "stack": "Stack trace string"
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true}`

---

### Dashboard & Analytics

#### `GET /api/dashboard`
- **Purpose**: Retrieves high-level KPIs, total sales, predicted demand, and system-wide chart data.
- **Required Role**: Any Authenticated User
- **Request Payload**: None
- **Response Format**:
  - **Success (200)**:
    ```json
    {
      "totalSales": 150000.0,
      "predictedDemand": 5400,
      "accuracy": "92.5%",
      "chartData": [
        {"date": "2023-10-01", "Actual Sales": 100, "AI Prediction": null}
      ],
      "smartWhy": "Recommendation text...",
      "productCount": 120,
      "forecast_unavailable": false
    }
    ```

#### `GET /api/warehouse/summary`
- **Purpose**: Retrieves warehouse summary statistics for a specific location.
- **Required Role**: Any Authenticated User (Must have access to the location or be Admin)
- **Query Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `location_id` | Integer | Yes | The ID of the location |
- **Response Format**:
  - **Success (200)**:
    ```json
    {
      "success": true,
      "location": { "id": 1, "loc_code": "WH1", "description": "Main Warehouse" },
      "data": {
        "total_sales": 5000.0,
        "total_items_sold": 150,
        "total_stock": 2000,
        "stock_by_category": [ { "category": "Electronics", "stock": 500 } ],
        "products": [ { "id": 1, "sku": "SKU-1", "name": "Prod 1", "category": "Cat", "current_stock": 10, "incoming_stock": 0 } ]
      }
    }
    ```
  - **Error (400/403/404)**: `{"success": false, "message": "Error details"}`

#### `GET /api/warehouse/product_stats`
- **Purpose**: Retrieves detailed statistics for a specific product at a specific location.
- **Required Role**: Any Authenticated User (Must have access to the location or be Admin)
- **Query Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `location_id` | Integer | Yes | The ID of the location |
  | `product_id` | Integer | Yes | The ID of the product |
- **Response Format**:
  - **Success (200)**: Detailed product statistics, historical sales array, and recent activities.

---

### Inventory & Products

#### `GET /api/inventory`
- **Purpose**: Retrieves a list of inventory products tailored to the user's assigned locations.
- **Required Role**: Any Authenticated User
- **Request Payload**: None
- **Response Format**:
  - **Success (200)**: Array of objects containing `id`, `sku_id`, `product_name`, `total_stock`, `ams_3m`, and `status`.

#### `GET /api/inventory/all`
- **Purpose**: Retrieves a system-wide list of all inventory products across all locations.
- **Required Role**: Any Authenticated User
- **Request Payload**: None
- **Response Format**:
  - **Success (200)**: Array of objects identical to `/api/inventory` but aggregated system-wide.

#### `GET /api/inventory/products/<sku>`
- **Purpose**: Retrieves detailed information for a specific product by SKU (Model Code).
- **Required Role**: Any Authenticated User
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `sku` | String | Yes | The model code (SKU) of the product |
- **Response Format**:
  - **Success (200)**: Complex JSON object detailing `product`, `stock_health`, `velocity`, `incoming`, `analytics`, `orders`, `forecast`, `locations`, `vendors`, and `pricing`.
  - **Error (404)**: `{"error": "Product not found"}`

#### `GET /api/inventory/location/<location_id>`
- **Purpose**: Retrieves products specifically stocked at a given location ID.
- **Required Role**: Any Authenticated User (Must have access to the location or be Admin/Manager)
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `location_id` | Integer | Yes | The location ID |
- **Response Format**:
  - **Success (200)**: Array of product objects including `quantity` and `ams_3m`.

#### `GET /api/inventory/<product_id>/locations`
- **Purpose**: Retrieves the specific locations and stock quantities for a single product (filtered by user assignment).
- **Required Role**: Any Authenticated User
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `product_id` | Integer | Yes | The product ID |
- **Response Format**:
  - **Success (200)**: Array of objects `{"location_name": "...", "location_code": "...", "type": "...", "quantity": 10}`

#### `GET /api/inventory/<product_id>/all_locations`
- **Purpose**: Retrieves stock quantities for a single product across ALL locations.
- **Required Role**: Any Authenticated User
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `product_id` | Integer | Yes | The product ID |
- **Response Format**:
  - **Success (200)**: Array of location objects identical to `/api/inventory/<product_id>/locations`.

#### `POST /api/products`
- **Purpose**: Adds a new product to the system.
- **Required Role**: Manager
- **Request Payload**:
  ```json
  {
    "model_code": "SKU-999",
    "product_name": "New Widget",
    "category": "Tools",
    "brand": "Acme",
    "status": "Active"
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Product added successfully", "id": 99}`
  - **Error (400/500)**: `{"success": false, "message": "Error description"}`

---

### Procurement & Orders

#### `GET /api/orders`
- **Purpose**: Retrieves a list of all purchase orders.
- **Required Role**: Any Authenticated User
- **Request Payload**: None
- **Response Format**:
  - **Success (200)**: Array of order objects including `id`, `po_reference`, `product_name`, `vendor_name`, `quantity`, `status`, `confirmation_status`, `created_at`, and `eta`.

#### `GET /api/orders/<order_id>`
- **Purpose**: Retrieves detailed information for a specific purchase order.
- **Required Role**: Any Authenticated User
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `order_id` | Integer | Yes | The ID of the order |
- **Response Format**:
  - **Success (200)**: Order object detailing product info, vendor info, timeline, and an `email_preview` string.

#### `POST /api/generate-pr`
- **Purpose**: Generates a new Purchase Request (PR) / Pending Order.
- **Required Role**: Warehouse
- **Request Payload**:
  ```json
  {
    "sku_id": "SKU-123",
    "quantity": 100,
    "vendor_id": 1,
    "ul_id": 5
  }
  ```
  *(Note: `vendor_id` is optional; `ul_id` corresponds to UserLocation ID)*
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Purchase Request created for SKU-123"}`
  - **Error (400/403/404/500)**: `{"success": false, "message": "Error details"}`

#### `POST /api/orders/<order_id>/confirm`
- **Purpose**: Confirms a pending purchase order, transitioning it to 'Ordered'.
- **Required Role**: Manager, Admin
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `order_id` | Integer | Yes | The ID of the order to confirm |
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Order confirmed successfully"}`

#### `POST /api/orders/<order_id>/receive`
- **Purpose**: Marks a 'Shipped' order as 'Received' and updates inventory.
- **Required Role**: Warehouse, Admin
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `order_id` | Integer | Yes | The ID of the order to receive |
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Order received successfully"}`
  - **Error (400)**: `{"success": false, "message": "Order must be Shipped before it can be received"}`

---

### Vendors

#### `GET /api/vendors`
- **Purpose**: Retrieves a list of all vendors.
- **Required Role**: Any Authenticated User
- **Response Format**:
  - **Success (200)**: Array of vendor objects `{"id": 1, "vendor_name": "...", "contact_person": "...", "phone_number": "...", "is_overseas": false}`

#### `POST /api/vendors`
- **Purpose**: Adds a new vendor to the system.
- **Required Role**: Manager
- **Request Payload**:
  ```json
  {
    "vendor_name": "Global Tech",
    "contact_person": "Jane Doe",
    "phone_number": "555-0199",
    "is_overseas": true
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Vendor added successfully", "id": 10}`

---

### Forecasting & AI Margin Simulator

#### `GET /api/forecast/locations`
- **Purpose**: Retrieves a list of locations for filtering the forecast.
- **Required Role**: Any Authenticated User
- **Response Format**:
  - **Success (200)**: Array of location objects `{"id": 1, "loc_code": "...", "description": "...", "type": "..."}`

#### `GET /api/forecast/products`
- **Purpose**: Retrieves products available for forecasting, optionally filtered by location.
- **Required Role**: Any Authenticated User
- **Query Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `location_id` | String/Int | No | The location ID or "ALL" |
- **Response Format**:
  - **Success (200)**: Array of product objects.

#### `GET /api/forecast/data`
- **Purpose**: Retrieves aggregated time-series forecast data, chart metrics, moving averages, and KPI alerts.
- **Required Role**: Any Authenticated User
- **Query Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `location_id` | String/Int | Yes | The location ID or "ALL" |
  | `product_id` | String/Int | Yes | The product ID or "ALL" |
  | `interval` | String | No | "daily", "weekly", "biweekly", "monthly" |
- **Response Format**:
  - **Success (200)**:
    ```json
    {
      "chartData": [
        {"date": "2023-10-01", "volume": 50, "MA3": 45.5, "MA7": 42.0, "MA14": 40.0}
      ],
      "kpi": { "TrendLogic": "Uptrend", "DemandMomentum": 0.05, "Volatility": 2.1, "CurrentStock": 100 },
      "alerts": [
        {"type": "info", "message": "Trend Alert: MA3 recently crossed above MA7 (Uptrend)."}
      ]
    }
    ```

#### `POST /api/margin-simulator/forecast`
- **Purpose**: Generates a margin simulation forecast using Nixtla TimeGEN for a specific proposed price.
- **Required Role**: Any Authenticated User
- **Request Payload**:
  ```json
  {
    "product_id": 1,
    "proposed_price": 49.99,
    "volume_discount": 5.0
  }
  ```
- **Response Format**:
  - **Success (200)**:
    ```json
    {
      "success": true,
      "actuals": [...],
      "forecast": [...],
      "total_predicted_volume": 500,
      "proposed_price": 47.49
    }
    ```

#### `POST /api/margin-simulator/chat`
- **Purpose**: Sends an agentic chat query to Azure OpenAI combining text and image.
- **Required Role**: Any Authenticated User
- **Request Payload**:
  ```json
  {
    "prompt": "Analyze this margin chart...",
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "rationale": "Markdown response text..."}`

---

### Sales Hub

#### `GET /api/sales`
- **Purpose**: Retrieves a list of all sales quotes and finalized sales.
- **Required Role**: Sales
- **Response Format**:
  - **Success (200)**: Array of sale objects.

#### `POST /api/sales`
- **Purpose**: Creates a new sale quotation.
- **Required Role**: Sales
- **Request Payload**:
  ```json
  {
    "pl_id": 1,
    "quantity_sold": 10,
    "customer_name": "Acme Corp",
    "client_email": "billing@acme.com",
    "price": 105.00
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Quotation sent successfully!", "sale_id": 5}`
  - **Error (400)**: `{"success": false, "message": "Insufficient stock"}`

#### `GET /api/sales/dashboard`
- **Purpose**: Retrieves KPIs, sales by location, and pipeline velocity for the Sales Dashboard.
- **Required Role**: Sales
- **Response Format**:
  - **Success (200)**:
    ```json
    {
      "personalSales": 5000.0,
      "teamSales": 150000.0,
      "salesByLocation": [ {"name": "Main Warehouse", "value": 2500.0} ],
      "pipelineVelocity": [ {"month": "OCT", "full_date": "2023-10", "sales": 5000.0} ]
    }
    ```

#### `PUT /api/sales/<sale_id>/status`
- **Purpose**: Updates the status of a sale (e.g., to 'Verified' or 'Paid'). When Verified, deducts stock and generates an invoice.
- **Required Role**: Sales
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `sale_id` | Integer | Yes | The ID of the sale |
- **Request Payload**:
  ```json
  {
    "status": "Verified"
  }
  ```
  *(Valid statuses: Quoted, Pending Verification, Verified, Paid)*
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Sale status updated to Verified"}`

#### `GET /api/invoices`
- **Purpose**: Retrieves a list of all invoices.
- **Required Role**: Sales
- **Response Format**:
  - **Success (200)**: Array of invoice objects `{"id": 1, "invoice_number": "INV-20231015-5", "total_amount": 1050.0, "date": "..."}`

#### `POST /api/invoices`
- **Purpose**: Manually generates a new invoice for a sale.
- **Required Role**: Sales
- **Request Payload**:
  ```json
  {
    "sale_id": 5,
    "invoice_number": "INV-20231015-5",
    "total_amount": 1050.0
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Invoice generated successfully", "invoice_id": 1}`

---

### Workspace, Team, & Mail

#### `GET /api/workspace/team`
- **Purpose**: Retrieves members of the workspace grouped by assigned locations.
- **Required Role**: Any Authenticated User
- **Response Format**:
  - **Success (200)**: `{"success": true, "team_grouped": [...]}` (for Managers/Admins) or `{"success": true, "team": [...]}` (for others).

#### `GET /api/workspace/users`
- **Purpose**: Retrieves a flat list of all users for assignment dropdowns.
- **Required Role**: Manager
- **Response Format**:
  - **Success (200)**: `{"success": true, "users": [ {"id": 1, "username": "...", "email": "...", "role": "..."} ]}`

#### `POST /api/users`
- **Purpose**: Creates a new user in the system.
- **Required Role**: Admin
- **Request Payload**:
  ```json
  {
    "username": "newuser",
    "email": "new@example.com",
    "password": "password",
    "role": "Sales"
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "User created successfully", "user_id": 10}`

#### `POST /api/assign-location`
- **Purpose**: Assigns a user to a specific location.
- **Required Role**: Manager
- **Request Payload**:
  ```json
  {
    "uid": 5,
    "location_id": 2
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Location assigned to user successfully", "ul_id": 12}`

#### `GET /api/workspace/mail/inbox`
- **Purpose**: Retrieves the current user's inbox messages.
- **Required Role**: Any Authenticated User
- **Response Format**:
  - **Success (200)**: `{"success": true, "mails": [...]}`

#### `GET /api/workspace/mail/sent`
- **Purpose**: Retrieves the current user's sent messages.
- **Required Role**: Any Authenticated User
- **Response Format**:
  - **Success (200)**: `{"success": true, "mails": [...]}`

#### `POST /api/workspace/mail/send`
- **Purpose**: Sends an internal mail message to another user.
- **Required Role**: Any Authenticated User
- **Request Payload**:
  ```json
  {
    "receiver_id": 2,
    "subject": "Stock Update",
    "body": "Please check the stock for SKU-123."
  }
  ```
- **Response Format**:
  - **Success (200)**: `{"success": true, "message": "Mail sent successfully"}`

#### `POST /api/workspace/mail/<mail_id>/read`
- **Purpose**: Marks an internal mail message as read.
- **Required Role**: Any Authenticated User
- **Path Parameters**:
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `mail_id` | Integer | Yes | The ID of the mail message |
- **Response Format**:
  - **Success (200)**: `{"success": true}`

---

### General Locations

#### `GET /api/locations`
- **Purpose**: Retrieves a list of locations assigned to the current user (or all locations if Admin/Manager). Includes address and region details.
- **Required Role**: Any Authenticated User
- **Response Format**:
  - **Success (200)**: Array of location objects `{"id": 1, "loc_code": "WH1", "description": "...", "type": "...", "address": "...", "region": "..."}`

---

### WebSockets

#### `generate_forecast_ws`
- **Purpose**: Streams progress and multi-horizon prediction data from Azure TimeGEN-1 based on historical data.
- **Event**: `generate_forecast_ws` (Client to Server)
- **Payload**: `{"historical_data": [{"date": "2023-10-01", "volume": 100}], "interval": "daily", "location_id": "ALL", "product_id": "ALL"}`
- **Server Emits**: `forecast_progress` (Updates), `forecast_complete` (Results), `forecast_error` (Failure).

#### `copilot_chat`
- **Purpose**: Communicates with the Azure AI Project agent to process procurement-related queries and return structured tool actions.
- **Event**: `copilot_chat` (Client to Server)
- **Payload**: `{"message": "I need 50 units of SKU-123", "sku": "SKU-123"}`
- **Server Emits**: `copilot_progress` (Updates), `copilot_response` (Parsed JSON Agent response), `copilot_error` (Failure).
