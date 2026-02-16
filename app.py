import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Inventory, Forecast, HistoricalSales, PurchaseRequest, Vendor

# Configure Flask to serve React build files
app = Flask(__name__, static_folder='frontend/dist')
app.config['SECRET_KEY'] = 'dev-secret-key' # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized'}), 401

# API: Login
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(username=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    login_user(user)
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'role': user.role})

# API: Logout
@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'success': True})

# API: Check Auth Status
@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'role': current_user.role, 'username': current_user.username})
    return jsonify({'authenticated': False}), 401

# API: Dashboard Data
@app.route('/api/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    # Mock aggregation for chart
    # In a real app, query HistoricalSales and Forecast tables
    chart_data = [
        { "date": "Jan", "Actual Sales": 4500, "AI Prediction": 4600 },
        { "date": "Feb", "Actual Sales": 5200, "AI Prediction": 5100 },
        { "date": "Mar", "Actual Sales": 4800, "AI Prediction": 4900 },
        { "date": "Apr", "Actual Sales": 6100, "AI Prediction": 5900 },
        { "date": "May", "Actual Sales": 5500, "AI Prediction": 5800 },
        { "date": "Jun", "Actual Sales": 6700, "AI Prediction": 6500 },
    ]

    # Example fetching product details for summary
    product_count = Product.query.count()

    data = {
        'totalSales': 32800,
        'predictedDemand': 34500,
        'accuracy': "94.2%",
        'chartData': chart_data,
        'smartWhy': "Demand is expected to rise by 12% in Q3 due to seasonal trends and competitor stock-outs in the region. Recommendation: Increase inventory for SKU-123 by 15%.",
        'productCount': product_count
    }
    return jsonify(data)

# API: Generate PR
@app.route('/api/generate-pr', methods=['POST'])
@login_required
def api_generate_pr():
    data = request.json
    sku_id = data.get('sku_id', 'SKU-123') # Default for demo
    quantity = data.get('quantity', 100)

    # Find product by SKU string or ID
    product = Product.query.filter_by(sku_id=sku_id).first()
    if not product:
         # Fallback to first product if SKU not found
        product = Product.query.first()

    if product:
        pr = PurchaseRequest(
            sku_id_fk=product.id,
            requested_quantity=int(quantity),
            status='Pending',
            created_by=current_user.id
        )
        db.session.add(pr)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Purchase Request created for {product.sku_id}'})

    return jsonify({'success': False, 'message': 'Product not found'}), 404

# API: Inventory List
@app.route('/api/inventory', methods=['GET'])
@login_required
def api_inventory():
    products = Product.query.all()
    inventory_list = []

    for product in products:
        # Calculate AMS (3-Month)
        cutoff_3m = datetime.utcnow() - timedelta(days=90)
        total_sales_3m = db.session.query(db.func.sum(HistoricalSales.quantity_sold)).filter(
            HistoricalSales.sku_id_fk == product.id,
            HistoricalSales.transaction_date >= cutoff_3m
        ).scalar() or 0
        ams_3m = round(total_sales_3m / 3, 1)

        inventory_list.append({
            'id': product.id,
            'sku_id': product.sku_id,
            'product_name': product.product_name,
            'total_stock': product.inventory.total_stock_on_hand if product.inventory else 0,
            'ams_3m': ams_3m,
            'status': product.stock_status
        })

    return jsonify(inventory_list)

# API: Product Detail
@app.route('/api/inventory/products/<path:sku>', methods=['GET'])
@login_required
def api_product_detail(sku):
    product = Product.query.filter_by(sku_id=sku).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Calculate AMS
    cutoff_3m = datetime.utcnow() - timedelta(days=90)
    total_sales_3m = db.session.query(db.func.sum(HistoricalSales.quantity_sold)).filter(
        HistoricalSales.sku_id_fk == product.id,
        HistoricalSales.transaction_date >= cutoff_3m
    ).scalar() or 0
    ams_3m = round(total_sales_3m / 3, 1)

    cutoff_6m = datetime.utcnow() - timedelta(days=180)
    total_sales_6m = db.session.query(db.func.sum(HistoricalSales.quantity_sold)).filter(
        HistoricalSales.sku_id_fk == product.id,
        HistoricalSales.transaction_date >= cutoff_6m
    ).scalar() or 0
    ams_6m = round(total_sales_6m / 6, 1)

    # Calculate Trend
    trend_percentage = 0
    if ams_6m > 0:
        trend_percentage = round(((ams_3m - ams_6m) / ams_6m) * 100, 1)

    # Coverage
    coverage = 0
    if ams_3m > 0 and product.inventory:
        coverage = round(product.inventory.total_stock_on_hand / ams_3m, 1)

    # Sales Channel Distribution
    sales_channels = db.session.query(
        HistoricalSales.sales_channel,
        db.func.sum(HistoricalSales.quantity_sold)
    ).filter(
        HistoricalSales.sku_id_fk == product.id
    ).group_by(HistoricalSales.sales_channel).all()

    distribution_data = [{'name': channel, 'value': quantity} for channel, quantity in sales_channels]

    # Sales Trend (Line Chart) - Last 6 months
    # Simplified aggregation by month
    sales_trend = []
    today = datetime.utcnow()
    for i in range(5, -1, -1):
        month_start = (today - timedelta(days=30*i)).replace(day=1)
        # Simple approximation for demo, ideally use proper date truncation
        month_end = month_start + timedelta(days=30)

        monthly_sales = db.session.query(db.func.sum(HistoricalSales.quantity_sold)).filter(
            HistoricalSales.sku_id_fk == product.id,
            HistoricalSales.transaction_date >= month_start,
            HistoricalSales.transaction_date < month_end
        ).scalar() or 0

        sales_trend.append({
            'date': month_start.strftime("%b"),
            'Actual Sales': monthly_sales,
            'Forecast': monthly_sales * 1.1 # Mock forecast slightly higher
        })

    # Purchase Requests
    prs = PurchaseRequest.query.filter_by(sku_id_fk=product.id).order_by(PurchaseRequest.timestamp.desc()).all()
    pr_data = [{
        'id': pr.id,
        'quantity': pr.requested_quantity,
        'status': pr.status,
        'date': pr.timestamp.strftime("%Y-%m-%d"),
        'eta': (pr.timestamp + timedelta(days=product.lead_time)).strftime("%Y-%m-%d") if pr.status == 'Approved' else 'N/A'
    } for pr in prs]

    data = {
        'product': {
            'name': product.product_name,
            'sku': product.sku_id,
            'category': product.category,
            'status': product.stock_status,
            'lead_time': product.lead_time
        },
        'stock_health': {
            'total_physical': product.inventory.total_stock_on_hand if product.inventory else 0,
            'reserved': 0, # Mock value
            'free_to_sell': product.inventory.total_stock_on_hand if product.inventory else 0 # Simplified
        },
        'velocity': {
            'ams_3m': ams_3m,
            'ams_6m': ams_6m,
            'trend_percentage': trend_percentage
        },
        'incoming': {
            'total_incoming': product.inventory.incoming_stock if product.inventory else 0,
            'next_eta': (datetime.utcnow() + timedelta(days=15)).strftime("%b %d"), # Mock ETA
            'stockout_risk': product.forecast.smart_why_rationale if product.forecast else "No immediate risk."
        },
        'analytics': {
            'coverage': coverage,
            'distribution': distribution_data,
            'sales_trend': sales_trend
        },
        'orders': pr_data,
        'forecast': {
            'rationale': product.forecast.smart_why_rationale if product.forecast else "No forecast available."
        }
    }

    return jsonify(data)

# Serve React App for all other routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
