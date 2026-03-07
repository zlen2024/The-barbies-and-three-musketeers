# ChinhinForcastingPro - Complete Architecture & Solution Walkthrough

## 1. Executive Summary
**ChinhinForcastingPro** is an enterprise-grade Procurement and Pricing intelligence platform. It replaces manual, disjointed spreadsheet processes with an automated, AI-driven engine. The platform specifically addresses two core supply chain pain points:
1.  **Business Challenge 4 (Procurement):** An "Intelligent Procurement Planning Agent" that utilizes predictive demand forecasting (via Azure TimeGEN-1) to eliminate the "Excel Guessing Game," automatically generating Purchase Requests (PRs) based on historical sales velocity.
2.  **Business Challenge 9 (Sales & Pricing):** An "AI Pricing Strategist" that dynamically recommends optimal quoting prices. It replaces "gut-feel" gambling by analyzing customer history, stock aging, and market demand to maximize profit margins.

---

## 2. Software Requirements Specification (SRS)

### 2.1 Functional Requirements

#### 2.1.1 AI Supply Chain Brain (Forecasting Module)
*   **FR-1:** The system must aggregate historical sales data (`SaleItem` quantities) across customizable time intervals (Daily, Weekly, Bi-weekly, Monthly).
*   **FR-2:** The system must integrate with Azure TimeGEN-1 via the `nixtla` SDK to generate 9-week future time-series predictions.
*   **FR-3:** The system must cache forecasting results in the database (`Forecast` table) as JSON arrays to prevent redundant external API calls and ensure sub-second dashboard load times.
*   **FR-4:** The system must automatically trigger background thread updates for stale forecasts using `threading.Lock()` to prevent duplicate concurrent API requests.
*   **FR-5:** The system must overlay statistical Moving Averages (MA3, MA7, MA14) against historical actuals on the frontend to provide immediate visual context.

#### 2.1.2 Automated PR Engine & Smart Approver Dashboard
*   **FR-6:** The system must allow users to auto-generate a Purchase Request (PR) directly from a Forecast view, calculating the required quantity based on current `quantity_on_hand` vs. `projected_demand`.
*   **FR-7:** PRs must be automatically routed to the correct Manager based on the `Location` of the requester.
*   **FR-8:** Managers must have a "Decision Cockpit" (Workspace) displaying instant context (e.g., Stock Coverage risk) to approve or reject PRs.
*   **FR-9:** Approved PRs must transition to a 'Confirmed' status, ready for Supplier generation.

#### 2.1.3 Dynamic Pricing Engine & Margin Simulator
*   **FR-10:** The Sales Hub must provide a quoting interface that links directly to real-time inventory levels (`ProductLoc`).
*   **FR-11:** The system must calculate a recommended optimal price based on base cost, regional pricing (`Pricing` table), and current stock aging.
*   **FR-12:** The system must provide a "Margin Simulator" allowing sales managers to visualize predicted revenue, profit amount, and margin percentage dynamically as they adjust the quote price.
*   **FR-13:** The system must provide a "Smart Why Rationale" explaining the logic behind the suggested price (e.g., highlighting aging inventory discounts).

#### 2.1.4 Role-Based Access Control (RBAC) & Internal Communication
*   **FR-14:** The system must enforce access control across five primary roles: Admin, Manager, Procurement, Warehouse, and Sales.
*   **FR-15:** Inventory visibility must be restricted based on the `UserLocation` mapping table (except for global Admin overrides).
*   **FR-16:** The system must include a native internal mail system (`InternalMail`) to allow cross-departmental communication without leaving the platform.

### 2.2 Non-Functional Requirements
*   **Security:** Enforce global HTTP security headers (HSTS, CSP, X-Frame-Options) via Flask `@app.after_request` hooks. Production secrets (e.g., `AZURE_TIMEGEN_API_KEY`) must be injected via environment variables. Session management relies on secure cookies via `flask_login`.
*   **Performance:** Complex aggregations (e.g., Average Monthly Sales) must utilize bulk SQL aggregation (e.g., `db.func.sum`) to prevent N+1 query bottlenecks in SQLite/Gunicorn environments.
*   **Resilience:** If the Azure TimeGEN API fails, the system must degrade gracefully, using local caching, logging the error, and setting a `forecast_unavailable` UI flag rather than crashing.

---

## 3. Software Design Description (SDD)

### 3.1 System Architecture

ChinhinForcastingPro utilizes a decoupled, three-tier architecture ensuring maintainability and scalability.

1.  **Presentation Tier (Frontend):**
    *   **Framework:** React.js bootstrapped with Vite for hot-module replacement and rapid bundling.
    *   **Styling & UI Components:** Tailwind CSS for utility-first styling. Tremor UI is utilized for specialized dashboard components (Cards, Metrics, layout grids). Headless UI is used for accessible interactive components (Modals, Dropdowns).
    *   **Charting:** Recharts is heavily utilized for complex, interactive data visualizations (e.g., resizable X-axes via `Brush` in the `ProductForecast.jsx` component) to overlay historical actuals, AI predictions, and Moving Averages without visual clipping.
    *   **State Management:** React Hooks (`useState`, `useEffect`) manage local component state. `localStorage` is used to persist user session data (`userRole`, `username`, `userId`) to drive conditional UI rendering (`ProtectedRoute` wrapper). Session data is used to pass temporary context between views (e.g., navigating to the Mail Composer).

2.  **Application Tier (Backend):**
    *   **Framework:** Python Flask providing RESTful API endpoints (`/api/*`).
    *   **Authentication:** `flask_login` manages secure user sessions using a `UserMixin` model.
    *   **Background Processing:** Time-consuming operations (like AI forecasting via `azure_forecast.py`) are offloaded to background threads. The `trigger_forecast_generation` function utilizes a `threading.Lock()` (`_generating_forecasts` set) to ensure that if multiple users request a forecast for the same product simultaneously, only one external API call is made. A custom `scheduler.py` runs tasks daily at midnight to pre-warm the cache.
    *   **AI Integration:** The `nixtla` SDK wraps calls to Azure TimeGEN-1. The system dynamically extracts the prediction column from the returned Pandas DataFrame to handle API version variations.

3.  **Data Tier (Database):**
    *   **ORM:** SQLAlchemy handles all database transactions and model definitions (`models.py`).
    *   **Database Engine:** SQLite is utilized for local development (`instance/inventory.db`), while Transact-SQL (T-SQL) is utilized for the production deployment environment (as detailed in `deployment_schema.md`).

### 3.2 Database Architecture

The database is highly relational, designed to support complex multi-location supply chain operations.

*   **Identity & Access Management:**
    *   `users`: Stores credentials and global `role`.
    *   `location`: Defines physical warehouses or online channels.
    *   `user_location`: A critical mapping table enforcing data visibility. A 'Warehouse' user only sees inventory for their assigned `location_id`.
*   **Product & Inventory Model:**
    *   `product`: Global catalog data (identified by `model_code`).
    *   `product_loc`: The granular source of truth for inventory. It tracks `quantity_on_hand` for a specific `product_id` at a specific `location_id`.
*   **Supply Chain & Procurement (Challenge 4 Focus):**
    *   `vendor` & `product_vendor`: Stores supplier lead times and cost bases.
    *   `product_order`: Manages the lifecycle of Purchase Requests (PRs) and Purchase Orders (POs), tracking `confirmation_status` from 'Pending' (needs approval) to 'Confirmed' (approved for order).
*   **Sales & Financials (Challenge 9 Focus):**
    *   `pricing`: Stores regional pricing tiers (e.g., West Malaysia vs. East Malaysia price).
    *   `sale` & `sale_item`: Transactional records. Creating a sale deducts `quantity` from the respective `product_loc`.
    *   `invoice`: Immutable billing records generated from confirmed sales.
*   **AI Analytics:**
    *   `forecast`: Caches the JSON string output of the Azure TimeGEN model alongside the `projected_demand` integer and the natural language `smart_why_rationale`.

---

## 4. Workflows & Data Flow

### 4.1 Workflow 1: The Intelligent Procurement Agent (Challenge 4)
*Goal: Move from manual Excel guessing to automated, AI-driven Purchase Requests.*

1.  **User Request:** A Procurement officer navigates to the Forecast dashboard and selects a product (e.g., "Kettles") and location. The frontend calls `/api/forecast/data?product_id=X&location_id=Y`.
2.  **Backend Cache Check:** `app.py` checks the `Forecast` table. If the data is missing or stale (older than 24 hours), it triggers the background thread (`azure_forecast.py`).
3.  **AI Aggregation:** The backend aggregates historical `SaleItem` data, zero-filling empty weeks, and sends a DataFrame to Azure TimeGEN-1 via the Nixtla SDK.
4.  **Presentation:** The frontend renders a `Recharts` ComposedChart showing historical actuals merging seamlessly into the AI prediction curve, accompanied by the "Smart Why Rationale" text.
5.  **Automated PR Generation:** The user clicks "Generate Purchase Request". The frontend sends a POST request to `/api/orders/generate_pr` containing the calculated demand shortfall.
6.  **Smart Approval:** The backend creates a `ProductOrder` with `confirmation_status='Pending'`. The assigned Manager receives an alert in their Workspace "Decision Cockpit", views the stock coverage context, and clicks "Approve", changing the status to 'Confirmed'.

### 4.2 Workflow 2: AI Pricing Strategist (Challenge 9)
*Goal: Recommend optimal pricing dynamically to maximize margin and sales velocity.*

1.  **Initiate Quote:** A Sales Manager opens the "Sales Hub" (`SalesHub.jsx`) and selects "New Quote".
2.  **Data Fetching:** The frontend pulls real-time `ProductLoc` data and base cost from `ProductVendor` via `/api/inventory` endpoints.
3.  **Dynamic Recommendation:** The frontend/backend logic analyzes current `quantity_on_hand` against recent sales velocity. If stock is aging (high quantity, low recent sales), the engine suggests a discounted price.
4.  **Margin Simulation:** The user types a prospective price into the UI. The frontend instantly calculates `(Price - Cost) * Quantity`, rendering a visual Badge indicating the predicted Profit Margin %.
5.  **Execution:** The user accepts the "Goldilocks" price. They submit the form, which hits `POST /api/sales`. The backend creates the `Sale` and `SaleItem`, immediately deducting stock from `ProductLoc`, and automatically generates an `Invoice` record.

---

## 5. User Guide & End-to-End Walkthrough

### 5.1 System Access
1.  **Launch Application:** Access the deployment URL or `http://localhost:5173` for local development.
2.  **Authentication:** The backend validates credentials against the `Users` table and sets a secure `flask_login` cookie. Session variables are passed to the frontend via `localStorage`.
    *   *Default Procurement/Admin Account:* `admin@inventory.ai` / `admin123`
    *   *Default Sales Account:* `sales@inventory.ai` / `sales123`

### 5.2 Navigating the Application
The Navigation Sidebar (`Layout.jsx`) conditionally renders based on the user's role:
*   **Dashboard:** High-level executive summary of KPIs (Total Revenue, Active PRs).
*   **Inventory List & Warehouse:** Granular view of `ProductLoc` stock levels.
*   **Forecast (Challenge 4):** Access the AI Supply Chain Brain for demand prediction.
*   **Sales Hub (Challenge 9):** Access the Quotation and Margin Simulation engine.
*   **Orders & Suppliers:** View lifecycle of `ProductOrder` records and manage `Vendor` data.
*   **Workspace:** Access Internal Mail, approve PRs, and view team hierarchies.

### 5.3 End-to-End Demonstration

**Phase 1: Procurement Optimization (Challenge 4)**
1.  Log in as **Admin/Procurement**.
2.  Click **Forecast** in the sidebar. Select a specific product to view its AI-predicted demand curve.
3.  Note the predicted demand volume and the "Smart Why" text explaining the seasonal trend.
4.  Click the **Generate PR** action button. Review the auto-calculated quantity needed to meet the AI's predicted demand. Submit the PR.
5.  Navigate to **Workspace** -> **Approvals**. You will see the PR waiting in the "Decision Cockpit". Click **Approve**. The order status updates seamlessly in the **Orders** tab.

**Phase 2: Maximizing Profit Margins (Challenge 9)**
1.  Log out, and log back in as **Sales**.
2.  Navigate to the **Sales Hub**. Click **New Quote**.
3.  Select a Customer, Location, and the Product you just procured.
4.  Observe the **AI Recommended Price**. Enter this price (or adjust it manually) into the unit price field.
5.  Watch the **Margin Simulator** dynamically update the predicted profit percentage.
6.  Click **Generate Quote/Sale**. The system records the transaction, updates the **Dashboard** revenue metrics in real-time, and generates an invoice, completing the cycle.
