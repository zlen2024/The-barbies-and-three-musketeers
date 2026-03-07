# ChinhinForcastingPro - Complete Documentation & Solution Walkthrough

## 1. Software Requirements Specification (SRS)

### 1.1 Purpose
The purpose of this document is to specify the software requirements for **ChinhinForcastingPro** (formerly InventoryAI), a comprehensive Procurement and Pricing intelligence platform. This system is designed to replace manual, spreadsheet-based procurement and pricing guesswork with an automated, AI-driven engine.

### 1.2 Scope
ChinhinForcastingPro solves two primary business challenges:
1. **Business Challenge 4 (Procurement):** Building an "Intelligent Procurement Planning Agent" that predicts stock needs based on historical sales velocity and seasonality, and automatically generates Purchase Requests (PRs).
2. **Business Challenge 9 (Sales & Pricing):** Building an "AI Pricing Strategist" that dynamically recommends optimal prices to maximize profit margins and sales velocity, replacing "gut-feel" gambling.

### 1.3 Overall Description
The system is a web-based application built using a React frontend (with Tremor and Tailwind CSS for UI) and a Python/Flask backend. It implements Role-Based Access Control (RBAC) to serve distinct workflows for Admin/Procurement, Warehouse, Sales, and Manager personas.

### 1.4 System Features

#### 1.4.1 AI Supply Chain Brain (Predictive Demand Forecasting)
*   **Description:** An AI model utilizing Azure TimeGEN-1 (via Nixtla) that analyzes historical sales data to auto-generate precise procurement plans by SKU and Location.
*   **Capabilities:**
    *   Dynamic interval forecasting (Daily, Weekly, Bi-weekly, Monthly).
    *   Moving Average (MA3, MA7, MA14) trend overlays.
    *   Natural language analysis prompts for deep-dive context ("Smart Why Rationale").

#### 1.4.2 Automated PR Engine & Smart Approver Dashboard
*   **Description:** Converts forecasted demand into actionable Purchase Requests.
*   **Capabilities:**
    *   Instant auto-generation of PRs routed to the correct approver based on location.
    *   A Decision Cockpit (Workspace/Manager Dashboard) that provides approvers with context (e.g., Stock Coverage, Risk levels) for faster decisions.

#### 1.4.3 Dynamic Pricing Engine & Margin Simulator
*   **Description:** An AI-driven module within the Sales Hub that recommends pricing strategies.
*   **Capabilities:**
    *   Instant analysis of customer history, stock aging, and market demand.
    *   Margin simulation tools allowing sales managers to visualize the predicted impact on revenue and profit prior to quoting.

---

## 2. Software Design Description (SDD)

### 2.1 System Architecture
The application follows a standard three-tier architecture:
1.  **Presentation Tier:** React.js frontend utilizing Tremor for data visualization (charts, KPIs) and Tailwind CSS for responsive styling. State management is handled via React Hooks and `localStorage` for session persistence.
2.  **Application Tier:** Python Flask RESTful API. It manages business logic, routing, role-based authentication (`flask_login`), and integration with external AI APIs (Azure TimeGEN via `nixtla` SDK). Long-running background forecasting tasks are handled via Python threading to unblock the main server.
3.  **Data Tier:** A relational database (SQLite for local development, T-SQL for production deployment) managed via SQLAlchemy ORM.

### 2.2 Database Architecture
The database is structured to support complex supply chain and sales operations across multiple locations.

#### Core Entity Relationships:
*   **Users & RBAC:** The `Users` table dictates access via the `role` attribute. The `UserLocation` table creates a many-to-many relationship mapping users to specific physical or online `Locations`, enforcing data-level visibility.
*   **Inventory Model:** The `Product` table holds global SKU data. The `ProductLoc` table maps products to locations, tracking `quantity_on_hand` at a granular level.
*   **Supply Chain:** `Vendors` are linked to products via `ProductVendor` (storing cost price and lead times). `ProductOrder` tracks the lifecycle of PRs and POs, linking back to the user and location.
*   **Sales & Pricing:** `Pricing` records establish base and regional prices. The `Sale` and `SaleItem` tables track actual transactions, reducing `ProductLoc` inventory upon completion. `Invoices` are generated from Sales.
*   **Forecasting Cache:** The `Forecast` table caches heavy AI prediction data (stored as JSON) and confidence scores to ensure fast dashboard load times without repeatedly hitting the external Azure API.

*(For the complete T-SQL deployment schema, refer to `deployment_schema.md` in the repository).*

---

## 3. User Guide

### 3.1 How to Login
1.  Navigate to the application URL (e.g., `http://localhost:5173` locally).
2.  Enter your credentials. Two default testing accounts are provisioned:
    *   **Procurement/Admin:** Email: `admin@inventory.ai` | Password: `admin123`
    *   **Sales:** Email: `sales@inventory.ai` | Password: `sales123`
3.  Click "Sign in". The system will route you to your role-specific dashboard.

### 3.2 Navigation & Roles
The left-hand sidebar adapts based on your role:
*   **Dashboard:** High-level metrics (Total Stock, Active PRs, Revenue).
*   **Inventory:** Live view of stock across locations.
*   **Forecast (Challenge 4):** The AI Demand Prediction engine.
*   **Sales Hub (Challenge 9):** Quotation, Invoicing, and Pricing Strategy.
*   **Orders:** Track Purchase Requests and Supplier Orders.
*   **Suppliers:** Vendor Management (Restricted to Admin/Manager/Procurement).
*   **Workspace:** Internal mail, team management, and PR approvals.

---

## 4. Solution Walkthrough

This section demonstrates how the system solves the two primary business challenges.

### 4.1 Solving Challenge 4: The Intelligent Procurement Agent
**Scenario:** A Procurement Officer needs to order stock for the upcoming month without playing the "Excel Guessing Game".

**Steps:**
1.  **AI Analysis:** The user navigates to the **Forecast** tab. They select a Location and a specific Product (e.g., "Kettles").
2.  **View Predictions:** The AI Supply Chain Brain queries historical data and displays a projected demand curve overlaid with historical actuals and Moving Averages.
3.  **Smart Rationale:** The system provides the "Smart Why" rationale, explaining *why* a certain volume is predicted (e.g., highlighting an upcoming seasonal spike).
4.  **Automated PR Generation:** Instead of manually calculating lead times and emailing suppliers, the user clicks **Generate Purchase Request** directly from the forecast view. The system auto-calculates the required quantity based on current `quantity_on_hand` vs. `projected_demand`.
5.  **Smart Approval:** The PR is routed to the **Workspace** of the relevant Manager. The Manager views the "Decision Cockpit", seeing instant context (Stock Coverage, Risk) and clicks "Approve" to finalize the order.

**Outcome:** The "Excel Trap" is eliminated. Inventory balance is maintained, and manual bottlenecks are removed.

### 4.2 Solving Challenge 9: AI Pricing Strategist
**Scenario:** A Sales Manager receives a bulk request from a dealer and needs to quote a price that wins the deal without sacrificing margin.

**Steps:**
1.  **Initiate Quote:** The user navigates to the **Sales Hub** and clicks "New Quote".
2.  **Dynamic Pricing Engine:** Upon selecting the customer and product, the system analyzes the customer's purchase history and current stock aging.
3.  **Margin Simulation:** The AI suggests an optimal price. The user can adjust the price in the simulator to immediately see the predicted impact on margin percentage and total profit.
4.  **Smart "Why":** The system explains the logic behind the suggested price (e.g., "Recommended 5% discount to clear aging inventory in Location A").
5.  **Finalize Deal:** Once the "Goldilocks" price is found, the user generates the Quote and immediately converts it to a formal Invoice.

**Outcome:** Replaces "Gut-Feel" gambling with data-driven pricing, shortens the decision cycle, and ensures maximum profit extraction from every deal.
