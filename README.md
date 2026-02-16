
# InventoryAI Flask Application with React Frontend

This is a prototype inventory management application built with Flask (Backend) and React (Frontend).

## Prerequisites

- Python 3.x
- Node.js (v18+) & npm

## Setup & Installation

### 1. Backend Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Linux/macOS
    source venv/bin/activate
    # Windows
    venv\Scripts\activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Seed the Database:**
    ```bash
    python seed_data.py
    ```

### 2. Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node dependencies:**
    ```bash
    npm install
    ```

3.  **Build the React application:**
    ```bash
    npm run build
    ```
    This will generate the production build in `frontend/dist`.

## Running the Application

1.  **Start the Flask Server:**
    Ensure you are in the root directory and the virtual environment is activated.
    ```bash
    python app.py
    ```

2.  **Access the Application:**
    Open your browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

3.  **Login Credentials:**
    *   **Procurement:** `admin@inventory.ai` / `admin123`
    *   **Sales:** `sales@inventory.ai` / `sales123`

## Features

-   **Dashboard:** Visualizes Historical Sales vs. AI Predictions using Tremor charts.
-   **Smart Why:** Natural language explanations for AI forecasts.
-   **Margin Simulator:** Test price changes and see impact on profit.
-   **PR Generator:** Automated Purchase Request generation.
-   **Role-Based Access:** Different views/actions for Sales and Procurement (simulated).

## API Endpoints

-   `POST /api/login` - User authentication
-   `GET /api/dashboard` - Dashboard data (KPIs, Charts)
-   `POST /api/generate-pr` - Generate Purchase Request
