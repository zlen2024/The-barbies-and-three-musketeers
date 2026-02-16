# InventoryAI Flask Application with React Frontend

This repository contains the InventoryAI platform, a Procurement & Pricing intelligence tool that combines a Flask backend with a modern React frontend (using Tremor & Tailwind CSS).

## 🚀 Quick Start (Production Mode)

This is the simplest way to run the full application as if it were deployed. The Flask server will serve the compiled React frontend.

1.  **Clone the Repository** & **Navigate to the directory**.

2.  **Backend Setup**:
    ```bash
    python -m venv venv
    # Linux/macOS
    source venv/bin/activate
    # Windows
    venv\Scripts\activate

    pip install -r requirements.txt
    python seed_data.py  # Initialize database
    ```

3.  **Frontend Build**:
    ```bash
    cd frontend
    npm install
    npm run build
    cd ..
    ```

4.  **Run the App**:
    ```bash
    python app.py
    ```
    Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🛠️ Development Setup (Hot-Reloading)

For active development, run the frontend and backend separately. This enables hot-reloading for React changes.

### 1. Start the Backend API

Open a terminal and run the Flask server. It will listen on port `5000`.

```bash
# Terminal 1
source venv/bin/activate
export FLASK_ENV=development  # Optional, enables debug mode
python app.py
```

### 2. Start the React Frontend

Open a **new terminal window** and run the Vite development server.

```bash
# Terminal 2
cd frontend
npm install  # If not already installed
npm run dev
```

The frontend will typically run on `http://localhost:5173`.
*   **API Requests**: The frontend is configured (via `vite.config.js`) to proxy `/api` requests to `http://127.0.0.1:5000`, preventing CORS issues during development.

---

## 🔑 Login Credentials

The seed data includes two default users for role-based access testing:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Procurement (Admin)** | `admin@inventory.ai` | `admin123` |
| **Sales** | `sales@inventory.ai` | `sales123` |

---

## 📦 Project Structure

```
├── app.py              # Main Flask application entry point
├── models.py           # SQLAlchemy Database Models
├── seed_data.py        # Script to populate the database
├── requirements.txt    # Python dependencies
├── instance/           # SQLite database location
└── frontend/           # React Application
    ├── src/
    │   ├── components/ # React components (Dashboard, Login)
    │   ├── App.jsx     # Main routing logic
    │   └── main.jsx    # Entry point
    ├── vite.config.js  # Vite configuration (proxy setup)
    └── tailwind.config.js # Styling configuration
```

##  troubleshooting

*   **Port 5000 in use:** If Flask fails to start, ensure no other service is using port 5000. You can kill the process or change the port in `app.py`.
*   **CORS Errors:** If you see CORS errors in the browser console during development, verify that the Vite proxy is working and that you are accessing the app via the Vite server URL (e.g., `localhost:5173`), not by opening HTML files directly.
*   **Database Errors:** If you encounter database schema errors, delete the `instance/inventory.db` file and re-run `python seed_data.py`.
