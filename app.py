import os
import math
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from functools import wraps
from sqlalchemy.orm import joinedload
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Location, ProductLoc, Vendor, ProductVendor, ProductOrder, Pricing, Campaign, Sale, SaleItem, Forecast, UserLocation, Invoice


# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure Flask to serve React build files
app = Flask(__name__, static_folder='frontend/dist')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Start the background forecast scheduler immediately upon app instantiation
# so it runs under gunicorn as well.
from scheduler import init_scheduler
init_scheduler()
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized'}), 401

@app.before_request
def log_request_info():
    if request.path.startswith('/api/'):
        user_info = "Anonymous"
        if current_user.is_authenticated:
            user_info = f"User: {current_user.username} (Role: {current_user.role}, ID: {current_user.id})"
        logger.info(f"Incoming Request: {request.method} {request.path} | {user_info}")


@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:;"
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the full stack trace
    logger.error(f"Unhandled Exception: {str(e)}\n{traceback.format_exc()}")
    # Return JSON for API routes
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'An internal server error occurred', 'error': str(e)}), 500
    # Otherwise render a generic error or just return string
    return "Internal Server Error", 500

# API: Client Logs
@app.route('/api/client-logs', methods=['POST'])
def api_client_logs():
    data = request.json or {}
    level = data.get('level', 'error').lower()
    message = data.get('message', 'Unknown client error')
    stack = data.get('stack', '')
    user_info = "Anonymous"
    if current_user.is_authenticated:
        user_info = f"User: {current_user.username} (Role: {current_user.role}, ID: {current_user.id})"

    log_msg = f"Client Log [{level.upper()}] - {user_info}: {message}"
    if stack:
        log_msg += f"\nStack: {stack}"

    if level == 'error':
        logger.error(log_msg)
    elif level == 'warn':
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    return jsonify({'success': True})


def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Unauthorized'}), 401
            if current_user.role not in roles:
                return jsonify({'error': 'Forbidden: Insufficient privileges'}), 403
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# API: Login
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username_or_email = data.get('email') # Frontend sends 'email' field
    password = data.get('password')

    # Try matching username first, then email
    user = User.query.filter_by(username=username_or_email).first()
    if not user:
        user = User.query.filter_by(email=username_or_email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    login_user(user)

    return jsonify({'success': True, 'role': user.role, 'username': user.username, 'email': user.email, 'user_id': user.id})

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
    # 1. Total Sales (Revenue Estimate)
    # Join Sale -> ProductLoc -> Product -> Pricing
    # This is complex in SQLAlchmey without proper primaryjoin if ambiguity exists, but let's try a simpler approach or direct join.
    # For MVP/Demo: Iterate sales or simple sum.

    # Let's just sum quantity for now as "Total Units Sold" or try to estimate revenue
    total_sales_units = db.session.query(db.func.sum(SaleItem.quantity)).scalar() or 0

    # Estimate Revenue: Get all sales, and for each, find the product's price.
    # Optimized to use a single SQL aggregate query instead of N+1 queries in Python.
    total_revenue = db.session.query(
        db.func.sum(SaleItem.quantity * Pricing.lsp_price)
    ).join(
        ProductLoc, SaleItem.pl_id == ProductLoc.id
    ).join(
        Pricing, ProductLoc.product_id == Pricing.product_id
    ).scalar() or 0

    # 2. Predicted Demand
    total_predicted_demand = db.session.query(db.func.sum(Forecast.projected_demand)).filter(Forecast.product_id != None).scalar() or 0

    # 3. Chart Data (Sales by Week)
    import json
    from scheduler import get_historical_sales_data

    chart_data = []

    # Get 140 days of historical data (weekly)
    historical_sales = get_historical_sales_data(product_id=None, days=140)
    for i, hs in enumerate(historical_sales):
        dt = datetime.strptime(hs['timestamp'], '%Y-%m-%d')
        # Only overlay the actuals on the AI Prediction line for the very last data point to ensure continuity
        is_last = (i == len(historical_sales) - 1)
        chart_data.append({
            'date': dt.strftime("%Y-%m-%d"),
            'Actual Sales': hs['value'],
            'AI Prediction': hs['value'] if is_last else None
        })

    # Check Azure Forecast from Database for System-wide (product_id = None)
    system_forecast = Forecast.query.filter_by(product_id=None).first()
    forecast_unavailable = True

    if system_forecast and system_forecast.forecast_data:
        try:
            forecast_results = json.loads(system_forecast.forecast_data)
            for f in forecast_results:
                f_date = datetime.strptime(f['date'], "%Y-%m-%d")
                chart_data.append({
                    'date': f_date.strftime("%Y-%m-%d"),
                    'Actual Sales': None,
                    'AI Prediction': f['value']
                })
            forecast_unavailable = False
        except Exception as e:
            logger.error(f"Error parsing system forecast data: {e}")

    if forecast_unavailable:
        logger.warning("System-wide forecast data not available. Triggering background generation.")
        from azure_forecast import trigger_forecast_generation
        trigger_forecast_generation(current_app, None, historical_sales)

    # 4. Product Count
    product_count = Product.query.count()

    data = {
        'totalSales': total_revenue, # Sending Value
        'predictedDemand': total_predicted_demand,
        'accuracy': "92.5%", # Mock
        'chartData': chart_data,
        'smartWhy': "Inventory turnover is optimal in Main Warehouse, but Online Channels are showing a 15% stockout risk for high-velocity items. Recommend rebalancing stock to channels.",
        'productCount': product_count,
        'forecast_unavailable': forecast_unavailable
    }
    return jsonify(data)

# API: Generate PR
@app.route('/api/generate-pr', methods=['POST'])
@login_required
@role_required('Warehouse')
def api_generate_pr():
    data = request.json
    sku_id = data.get('sku_id', 'SKU-123')
    quantity = data.get('quantity', 100)

    # Find product by model_code
    product = Product.query.filter_by(model_code=sku_id).first()
    if not product:
         # Fallback to first product if SKU not found (for demo resilience)
        product = Product.query.first()

    if product:
        # Select vendor
        vendor_id = data.get('vendor_id')
        if vendor_id:
            pv = ProductVendor.query.filter_by(product_id=product.id, vendor_id=vendor_id).first()
        else:
            # Auto-select a vendor (in real app, user selects)
            pv = ProductVendor.query.filter_by(product_id=product.id).first()

        if not pv:
            return jsonify({'success': False, 'message': 'No vendor found for this product'}), 400

        ul_id = data.get('ul_id')
        if not ul_id:
            return jsonify({'success': False, 'message': 'ul_id is required to create a Product Order'}), 400

        # Verify ul_id exists and belongs to current user
        user_loc = UserLocation.query.filter_by(ul_id=ul_id, uid=current_user.id).first()
        if not user_loc:
            return jsonify({'success': False, 'message': 'Invalid User Location (ul_id) or unauthorized access'}), 403

        pr = ProductOrder(
            pv_id=pv.id,
            ul_id=ul_id,
            order_qty=int(quantity),
            status='Pending',
            confirmation_status='Pending', # Acts as PR
            created_by=current_user.id
        )
        try:
            db.session.add(pr)
            db.session.commit()
            logger.info(f"Purchase Request created successfully for {product.model_code} by user {current_user.username}")
            return jsonify({'success': True, 'message': f'Purchase Request created for {product.model_code}'})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create Purchase Request for {product.model_code}: {str(e)}\n")
            return jsonify({'success': False, 'message': 'Database error occurred while creating Purchase Request'}), 500

    return jsonify({'success': False, 'message': 'Product not found'}), 404

# Helper functions for calculations
def _calculate_ams_bulk(days):
    cutoff = datetime.now() - timedelta(days=days)
    sales_data = db.session.query(
        ProductLoc.product_id,
        db.func.sum(SaleItem.quantity)
    ).join(
        SaleItem, ProductLoc.id == SaleItem.pl_id
    ).join(
        Sale, Sale.id == SaleItem.sale_id
    ).filter(
        Sale.sale_date >= cutoff
    ).group_by(
        ProductLoc.product_id
    ).all()

    return {product_id: round((total_sales or 0) / (days / 30), 1) for product_id, total_sales in sales_data}

def _calculate_ams(product_id, days):
    cutoff = datetime.now() - timedelta(days=days)
    total_sales = db.session.query(db.func.sum(SaleItem.quantity)).join(Sale, Sale.id == SaleItem.sale_id).join(ProductLoc, ProductLoc.id == SaleItem.pl_id).filter(
        ProductLoc.product_id == product_id,
        Sale.sale_date >= cutoff
    ).scalar() or 0
    return round(total_sales / (days / 30), 1)

def _get_sales_distribution(product_id):
    sales_channels = db.session.query(
        Location.description,
        db.func.sum(SaleItem.quantity)
    ).join(ProductLoc, ProductLoc.location_id == Location.id).join(SaleItem, SaleItem.pl_id == ProductLoc.id).join(Sale, Sale.id == SaleItem.sale_id).filter(
        ProductLoc.product_id == product_id
    ).group_by(Location.description).all()

    return [{'name': channel, 'value': quantity} for channel, quantity in sales_channels]

def _get_monthly_sales_trend(product_id):
    import json
    from scheduler import get_historical_sales_data

    sales_trend = []

    # 1. Get 140 days of historical data (weekly)
    historical_sales = get_historical_sales_data(product_id=product_id, days=140)
    for i, hs in enumerate(historical_sales):
        dt = datetime.strptime(hs['timestamp'], '%Y-%m-%d')
        # Only overlay the actuals on the Forecast line for the very last data point to ensure continuity
        is_last = (i == len(historical_sales) - 1)
        sales_trend.append({
            'date': dt.strftime("%Y-%m-%d"),
            'Actual Sales': hs['value'],
            'Forecast': hs['value'] if is_last else None
        })

    # 2. Get forecast data from database
    product_forecast = Forecast.query.filter_by(product_id=product_id).first()
    forecast_unavailable = True

    if product_forecast and product_forecast.forecast_data:
        try:
            forecast_results = json.loads(product_forecast.forecast_data)
            for f in forecast_results:
                f_date = datetime.strptime(f['date'], "%Y-%m-%d")
                sales_trend.append({
                    'date': f_date.strftime("%Y-%m-%d"),
                    'Actual Sales': None,
                    'Forecast': f['value']
                })
            forecast_unavailable = False
        except Exception as e:
            logger.error(f"Error parsing product forecast data for product_id={product_id}: {e}")

    if forecast_unavailable:
        logger.warning(f"Forecast data not available for product_id={product_id}. Triggering background generation.")
        from azure_forecast import trigger_forecast_generation
        trigger_forecast_generation(current_app, product_id, historical_sales)

    return sales_trend, forecast_unavailable

def _get_order_summary(product):
    orders = db.session.query(ProductOrder).join(ProductVendor).filter(
        ProductVendor.product_id == product.id
    ).order_by(ProductOrder.created_at.desc()).all()

    avg_lead_time = 0
    if product.product_vendors:
        avg_lead_time = sum([pv.lead_time_days for pv in product.product_vendors]) / len(product.product_vendors)

    pr_data = [{
        'id': order.id,
        'quantity': order.order_qty,
        'status': order.status if order.confirmation_status == 'Confirmed' else 'Pending Approval',
        'date': order.created_at.strftime("%Y-%m-%d") if order.created_at else '',
        'eta': order.ets_date.strftime("%Y-%m-%d") if order.ets_date else 'N/A'
    } for order in orders]

    total_incoming = sum([o.order_qty for o in orders if o.status == 'Ordered'])

    return pr_data, int(avg_lead_time), total_incoming

# API: Inventory List
@app.route('/api/inventory', methods=['GET'])
@login_required
def api_inventory():
    products = Product.query.all()
    inventory_list = []
    ams_bulk = _calculate_ams_bulk(90)

    # Pre-fetch user locations if not Admin/Manager
    user_location_ids = None
    if current_user.role not in ['Admin', 'Manager']:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        user_location_ids = [ul.location_id for ul in user_locs]

    for product in products:
        # Calculate AMS (3-Month) using bulk data
        ams_3m = ams_bulk.get(product.id, 0.0)

        # Calculate stock based on user's assigned locations
        if user_location_ids is not None:
            stock = sum(pl.quantity_on_hand for pl in product.product_locs if pl.location_id in user_location_ids)
        else:
            stock = product.total_stock

        # Status Logic
        if stock == 0:
            status_display = "Critical"
        elif stock < 50:
            status_display = "Low Stock"
        else:
            status_display = "In Stock"

        inventory_list.append({
            'id': product.id,
            'sku_id': product.model_code,
            'product_name': product.product_name,
            'total_stock': stock,
            'ams_3m': ams_3m,
            'status': status_display
        })

    return jsonify(inventory_list)

# API: Get All Products Inventory Overview
@app.route('/api/inventory/all', methods=['GET'])
@login_required
def api_inventory_all():
    products = Product.query.all()
    inventory_list = []
    ams_bulk = _calculate_ams_bulk(90)

    for product in products:
        # Calculate AMS (3-Month) using bulk data
        ams_3m = ams_bulk.get(product.id, 0.0)

        # Calculate stock across all locations
        stock = product.total_stock

        # Status Logic
        if stock == 0:
            status_display = "Critical"
        elif stock < 50:
            status_display = "Low Stock"
        else:
            status_display = "In Stock"

        inventory_list.append({
            'id': product.id,
            'sku_id': product.model_code,
            'product_name': product.product_name,
            'total_stock': stock,
            'ams_3m': ams_3m,
            'status': status_display
        })

    return jsonify(inventory_list)

from azure_margin_simulator import generate_margin_simulation

# API: Margin Simulator Forecast
@app.route('/api/margin-simulator/forecast', methods=['POST'])
@login_required
def api_margin_simulator_forecast():
    data = request.json
    product_id = data.get('product_id')
    proposed_price = data.get('proposed_price')
    volume_discount = data.get('volume_discount', 0.0)

    if not product_id or proposed_price is None:
        return jsonify({'success': False, 'message': 'product_id and proposed_price are required'}), 400

    final_price = float(proposed_price) * (1 - (float(volume_discount) / 100.0))

    try:
        # Get historical sales data aggregated by week
        # We need: unique_id (model_code), timestamp (weekly start), value (quantity), price (avg unit_price)

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404

        unique_id = product.model_code

        # We fetch daily data first and group by week in pandas for convenience
        sales_data_raw = db.session.query(
            db.func.date(Sale.sale_date).label('date'),
            db.func.sum(SaleItem.quantity).label('total_quantity'),
            db.func.sum(SaleItem.subtotal).label('total_subtotal')
        ) \
        .join(SaleItem, SaleItem.sale_id == Sale.id) \
        .join(ProductLoc, ProductLoc.id == SaleItem.pl_id) \
        .filter(ProductLoc.product_id == product_id) \
        .group_by(db.func.date(Sale.sale_date)).all()

        import pandas as pd
        if not sales_data_raw:
            return jsonify({'success': False, 'message': 'No sales history available to run simulation.'}), 400

        df = pd.DataFrame([{
            'date': item.date,
            'quantity': item.total_quantity,
            'subtotal': item.total_subtotal
        } for item in sales_data_raw])

        df['date'] = pd.to_datetime(df['date'])

        # Resample to weekly
        df.set_index('date', inplace=True)
        weekly_df = df.resample('W').sum()
        weekly_df.reset_index(inplace=True)

        # Calculate weekly average price
        # Prevent division by zero
        weekly_df['price'] = weekly_df.apply(lambda row: row['subtotal'] / row['quantity'] if row['quantity'] > 0 else 0, axis=1)

        # Format for Nixtla TimeGEN
        sales_data = []
        for index, row in weekly_df.iterrows():
            if row['quantity'] > 0: # Or include 0 if you want dense data
                sales_data.append({
                    'unique_id': unique_id,
                    'timestamp': row['date'].strftime('%Y-%m-%d'),
                    'value': row['quantity'],
                    'price': row['price']
                })

        if not sales_data:
            return jsonify({'success': False, 'message': 'No weekly sales data available to run simulation.'}), 400

        # Add 0-filled weeks up to today to ensure we forecast from today forward
        today = datetime.now()
        last_date = pd.to_datetime(sales_data[-1]['timestamp'])

        while last_date < today - pd.Timedelta(days=7):
            last_date += pd.Timedelta(days=7)
            sales_data.append({
                'unique_id': unique_id,
                'timestamp': last_date.strftime('%Y-%m-%d'),
                'value': 0,
                'price': sales_data[-1]['price'] # carry forward last known price
            })

        # Ensure we have at least a few data points
        if len(sales_data) < 10:
             logger.warning(f"Very few data points ({len(sales_data)}) for product_id={product_id}. The forecast might be inaccurate.")

        # Call the simulation
        simulation_result = generate_margin_simulation(product_id, sales_data, final_price)

        if "error" in simulation_result:
            return jsonify({'success': False, 'message': simulation_result["error"]}), 500

        # Return the actuals (historical) alongside the forecast
        actuals = [{
            "date": d['timestamp'],
            "actual": d['value'],
            "price": d['price']
        } for d in sales_data]

        return jsonify({
            'success': True,
            'actuals': actuals,
            'forecast': simulation_result['forecast'],
            'total_predicted_volume': simulation_result['total_volume'],
            'proposed_price': final_price
        })

    except Exception as e:
        logger.error(f"Error generating margin simulator forecast: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Server error generating simulation.'}), 500

from azure_margin_agent import generate_agentic_rationale

# API: Margin Simulator Agentic Chat
@app.route('/api/margin-simulator/chat', methods=['POST'])
@login_required
def api_margin_simulator_chat():
    data = request.json
    prompt = data.get('prompt')
    image_base64 = data.get('image_base64')

    if not prompt or not image_base64:
        return jsonify({'success': False, 'message': 'prompt and image_base64 are required'}), 400

    # Ensure it doesn't include the data:image/png;base64, prefix if it does
    if image_base64.startswith('data:image'):
        image_base64 = image_base64.split('base64,')[1]

    try:
        result = generate_agentic_rationale(prompt, image_base64)
        if "error" in result:
             return jsonify({'success': False, 'message': result["error"]}), 500

        return jsonify({
            'success': True,
            'rationale': result['rationale']
        })
    except Exception as e:
        logger.error(f"Error in margin simulator chat: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error generating rationale.'}), 500


# API: Add Product
@app.route('/api/products', methods=['POST'])
@login_required
@role_required('Manager')
def api_add_product():
    data = request.json
    model_code = data.get('model_code')
    product_name = data.get('product_name')
    category = data.get('category')
    brand = data.get('brand')
    status = data.get('status', 'Active')

    if not model_code or not product_name:
        return jsonify({'success': False, 'message': 'Model Code and Product Name are required'}), 400

    existing_product = Product.query.filter_by(model_code=model_code).first()
    if existing_product:
        return jsonify({'success': False, 'message': 'Product with this Model Code already exists'}), 400

    new_product = Product(
        model_code=model_code,
        product_name=product_name,
        category=category,
        brand=brand,
        status=status
    )
    try:
        db.session.add(new_product)
        db.session.commit()
        logger.info(f"Product added successfully: {model_code} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Product added successfully', 'id': new_product.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add Product {model_code}: {str(e)}\n")
        return jsonify({'success': False, 'message': 'Database error occurred while adding Product'}), 500

# API: Get Vendors
@app.route('/api/vendors', methods=['GET'])
@login_required
def api_get_vendors():
    vendors = Vendor.query.all()
    vendor_list = [{
        'id': v.id,
        'vendor_name': v.vendor_name,
        'contact_person': v.contact_person,
        'phone_number': v.phone_number,
        'is_overseas': v.is_overseas
    } for v in vendors]
    return jsonify(vendor_list)

# API: Add Vendor
@app.route('/api/vendors', methods=['POST'])
@login_required
@role_required('Manager')
def api_add_vendor():
    data = request.json
    vendor_name = data.get('vendor_name')
    contact_person = data.get('contact_person')
    phone_number = data.get('phone_number')
    is_overseas = data.get('is_overseas', False)

    if not vendor_name:
        return jsonify({'success': False, 'message': 'Vendor Name is required'}), 400

    new_vendor = Vendor(
        vendor_name=vendor_name,
        contact_person=contact_person,
        phone_number=phone_number,
        is_overseas=is_overseas
    )
    try:
        db.session.add(new_vendor)
        db.session.commit()
        logger.info(f"Vendor added successfully: {vendor_name} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Vendor added successfully', 'id': new_vendor.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add Vendor {vendor_name}: {str(e)}\n")
        return jsonify({'success': False, 'message': 'Database error occurred while adding Vendor'}), 500

# API: Product Detail
@app.route('/api/inventory/products/<path:sku>', methods=['GET'])
@login_required
def api_product_detail(sku):
    product = Product.query.filter_by(model_code=sku).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Calculate velocity and health stats
    ams_3m = _calculate_ams(product.id, 90)
    ams_6m = _calculate_ams(product.id, 180)
    trend_percentage = round(((ams_3m - ams_6m) / ams_6m * 100), 1) if ams_6m > 0 else 0

    user_location_ids = None
    if current_user.role not in ['Admin', 'Manager']:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        user_location_ids = [ul.location_id for ul in user_locs]

    if user_location_ids is not None:
        stock = sum(pl.quantity_on_hand for pl in product.product_locs if pl.location_id in user_location_ids)
    else:
        stock = product.total_stock

    coverage = round(stock / ams_3m, 1) if ams_3m > 0 else 0

    # Fetch complex data structures via helpers
    distribution_data = _get_sales_distribution(product.id)
    sales_trend, forecast_unavailable = _get_monthly_sales_trend(product.id)
    pr_data, avg_lead_time, total_incoming = _get_order_summary(product)

    # Simple data mappings
    location_stock = []
    for pl in product.product_locs:
        if user_location_ids is not None and pl.location_id not in user_location_ids:
            continue
        location_stock.append({
            'location': pl.location.description,
            'type': pl.location.type,
            'quantity': pl.quantity_on_hand
        })

    vendor_info = [{
        'id': pv.vendor_id,
        'name': pv.vendor.vendor_name,
        'cost': pv.cost_price,
        'lead_time': pv.lead_time_days
    } for pv in product.product_vendors]

    pricing_info = {
        'lsp': product.pricing[0].lsp_price,
        'wm': product.pricing[0].wm_price,
        'em': product.pricing[0].em_price
    } if product.pricing else {}

    data = {
        'product': {
            'name': product.product_name,
            'sku': product.model_code,
            'category': product.category,
            'status': "In Stock" if stock > 0 else "Critical",
            'lead_time': avg_lead_time
        },
        'stock_health': {
            'total_physical': stock,
            'reserved': 0,
            'free_to_sell': stock
        },
        'velocity': {
            'ams_3m': ams_3m,
            'ams_6m': ams_6m,
            'trend_percentage': trend_percentage
        },
        'incoming': {
            'total_incoming': total_incoming,
            'next_eta': "TBD",
            'stockout_risk': product.forecast.smart_why_rationale if product.forecast else "No immediate risk."
        },
        'analytics': {
            'coverage': coverage,
            'distribution': distribution_data,
            'sales_trend': sales_trend
        },
        'orders': pr_data,
        'forecast': {
            'rationale': product.forecast.smart_why_rationale if product.forecast else "No forecast available.",
            'forecast_unavailable': forecast_unavailable
        },
        'locations': location_stock,
        'vendors': vendor_info,
        'pricing': pricing_info
    }

    return jsonify(data)

# API: Get Products for a Specific Location (for inventory location view)
@app.route('/api/inventory/location/<int:location_id>', methods=['GET'])
@login_required
def api_inventory_location(location_id):
    # Check access control for location if not Admin/Manager
    if current_user.role not in ['Admin', 'Manager']:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        user_location_ids = [ul.location_id for ul in user_locs]
        if location_id not in user_location_ids:
            return jsonify({'error': 'Forbidden access to this location'}), 403

    location = Location.query.get(location_id)
    if not location:
        return jsonify({'error': 'Location not found'}), 404

    # Get all product_loc records for this location
    product_locs = ProductLoc.query.filter_by(location_id=location_id).all()

    products_data = []
    ams_bulk = _calculate_ams_bulk(90)
    for pl in product_locs:
        product = pl.product

        # Calculate AMS (Average Monthly Sales) for this product
        # NOTE: Ideally AMS would be location-specific, but the existing _calculate_ams
        # calculates globally. We'll use the global one for consistency or just omit.
        # For now, using global AMS computed efficiently via bulk.
        ams = ams_bulk.get(product.id, 0.0)

        products_data.append({
            'id': product.id,
            'sku_id': product.model_code,
            'product_name': product.product_name,
            'category': product.category,
            'brand': product.brand,
            'status': product.status,
            'quantity': pl.quantity_on_hand,
            'ams_3m': ams,
        })

    return jsonify(products_data)


# API: Get Locations for Product (for inventory expanded row)
@app.route('/api/inventory/<int:product_id>/locations', methods=['GET'])
@login_required
def api_product_locations(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    user_location_ids = None
    if current_user.role not in ['Admin', 'Manager']:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        user_location_ids = [ul.location_id for ul in user_locs]

    location_data = []
    for pl in product.product_locs:
        if user_location_ids is not None and pl.location_id not in user_location_ids:
            continue

        location_data.append({
            'location_name': pl.location.description,
            'location_code': pl.location.loc_code,
            'type': pl.location.type,
            'quantity': pl.quantity_on_hand
        })
    return jsonify(location_data)

# API: Get Product Stock in ALL Locations
@app.route('/api/inventory/<int:product_id>/all_locations', methods=['GET'])
@login_required
def api_product_all_locations(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    location_data = []
    for pl in product.product_locs:
        location_data.append({
            'location_name': pl.location.description,
            'location_code': pl.location.loc_code,
            'type': pl.location.type,
            'quantity': pl.quantity_on_hand
        })
    return jsonify(location_data)

# API: Get All Orders
@app.route('/api/orders', methods=['GET'])
@login_required
def api_get_orders():
    # Join ProductOrder -> ProductVendor -> Product & Vendor
    orders = ProductOrder.query.options(
        joinedload(ProductOrder.product_vendor).joinedload(ProductVendor.product),
        joinedload(ProductOrder.product_vendor).joinedload(ProductVendor.vendor)
    ).order_by(ProductOrder.created_at.desc()).all()

    order_list = []
    for o in orders:
        pv = o.product_vendor
        prod = pv.product
        vend = pv.vendor

        order_list.append({
            'id': o.id,
            'po_reference': o.po_reference or f"PO-{o.id}",
            'product_name': prod.product_name,
            'vendor_name': vend.vendor_name,
            'quantity': o.order_qty,
            'status': o.status,
            'confirmation_status': o.confirmation_status,
            'created_at': o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
            'eta': o.ets_date.strftime("%Y-%m-%d") if o.ets_date else "TBD"
        })
    return jsonify(order_list)

# API: Get Order Detail
@app.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def api_order_detail(order_id):
    order = ProductOrder.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    pv = order.product_vendor
    prod = pv.product
    vend = pv.vendor

    # Timeline Logic
    # 1. Created (created_at)
    # 2. Confirmed (if confirmation_status == 'Confirmed')
    # 3. Shipped (if status == 'Shipped')
    # 4. Received (if status == 'Received')

    timeline = []
    if order.created_at:
        timeline.append({'stage': 'Created', 'date': order.created_at.strftime("%Y-%m-%d %H:%M"), 'completed': True})

    is_confirmed = order.confirmation_status == 'Confirmed'
    timeline.append({'stage': 'Confirmed', 'date': '', 'completed': is_confirmed})

    is_shipped = order.status in ['Shipped', 'Received']
    timeline.append({'stage': 'Shipped', 'date': '', 'completed': is_shipped})

    is_received = order.status == 'Received'
    timeline.append({'stage': 'Received', 'date': order.ets_date.strftime("%Y-%m-%d") if order.ets_date else '', 'completed': is_received})

    data = {
        'id': order.id,
        'po_reference': order.po_reference or f"PO-{order.id}",
        'product': {
            'name': prod.product_name,
            'sku': prod.model_code,
            'id': prod.id
        },
        'vendor': {
            'name': vend.vendor_name,
            'contact': vend.contact_person,
            'email': f"orders@{vend.vendor_name.lower().replace(' ', '')}.com" # Mock email
        },
        'quantity': order.order_qty,
        'status': order.status,
        'confirmation_status': order.confirmation_status,
        'created_at': order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "",
        'timeline': timeline,
        'email_preview': f"Dear {vend.contact_person or 'Sales Team'},\n\nPlease find attached Purchase Order PO-{order.id} for {order.order_qty} units of {prod.product_name} ({prod.model_code}).\n\nKindly confirm receipt and estimated delivery date.\n\nBest regards,\nProcurement Manager"
    }
    return jsonify(data)

# API: Confirm Order

@app.route('/api/orders/<int:order_id>/receive', methods=['POST'])
@login_required
@role_required('Warehouse', 'Admin')
def api_receive_order(order_id):
    order = ProductOrder.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.status == 'Received':
         return jsonify({'success': False, 'message': 'Order already received'}), 400

    if order.status != 'Shipped':
         return jsonify({'success': False, 'message': 'Order must be Shipped before it can be received'}), 400

    order.status = 'Received'

    # Update inventory
    pv = order.product_vendor
    ul = UserLocation.query.get(order.ul_id)
    location_id = ul.location_id

    product_loc = ProductLoc.query.filter_by(product_id=pv.product_id, location_id=location_id).first()
    if product_loc:
        product_loc.quantity += order.order_qty
        product_loc.last_updated = datetime.utcnow()
    else:
        product_loc = ProductLoc(product_id=pv.product_id, location_id=location_id, quantity=order.order_qty, reorder_point=0)
        db.session.add(product_loc)

    try:
        db.session.commit()
        logger.info(f"Order received successfully: ID {order_id} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Order received successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error receiving order {order_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/confirm', methods=['POST'])
@login_required
@role_required('Manager', 'Admin')
def api_confirm_order(order_id):
    order = ProductOrder.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.confirmation_status == 'Confirmed':
         return jsonify({'success': False, 'message': 'Order already confirmed'}), 400

    order.confirmation_status = 'Confirmed'
    order.status = 'Ordered' # Set initial status to Ordered once confirmed
    # Set ETA mock
    order.ets_date = datetime.utcnow() + timedelta(days=order.product_vendor.lead_time_days or 14)

    try:
        db.session.commit()
        logger.info(f"Order confirmed successfully: ID {order_id} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Order confirmed successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to confirm Order ID {order_id}: {str(e)}\n")
        return jsonify({'success': False, 'message': 'Database error occurred while confirming Order'}), 500

# API: Get Locations
@app.route('/api/forecast/locations', methods=['GET'])
@login_required
def api_forecast_locations():
    if current_user.role in ['Manager', 'Admin']:
        locations = Location.query.all()
    else:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        locations = [ul.location for ul in user_locs]

    location_list = [{
        'id': loc.id,
        'loc_code': loc.loc_code,
        'description': loc.description,
        'type': loc.type
    } for loc in locations]
    return jsonify(location_list)

# API: Get Locations for User
@app.route('/api/locations', methods=['GET'])
@login_required
def api_locations():
    # If manager or admin, return all, otherwise return assigned
    if current_user.role in ['Manager', 'Admin']:
        locations = Location.query.all()
    else:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        locations = [ul.location for ul in user_locs]

    location_list = [{
        'id': loc.id,
        'loc_code': loc.loc_code,
        'description': loc.description,
        'type': loc.type,
        'address': loc.address,
        'region': loc.region
    } for loc in locations]
    return jsonify(location_list)

# API: Get Products for Location
@app.route('/api/forecast/products', methods=['GET'])
@login_required
def api_forecast_products():
    location_id = request.args.get('location_id')

    if current_user.role in ['Manager', 'Admin']:
        allowed_location_ids = [loc.id for loc in Location.query.all()]
    else:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        allowed_location_ids = [ul.location_id for ul in user_locs]

    if location_id and location_id != 'ALL':
        try:
            loc_id_int = int(location_id)
            if loc_id_int not in allowed_location_ids:
                return jsonify({'error': 'Unauthorized location'}), 403
            target_location_ids = [loc_id_int]
        except ValueError:
            target_location_ids = allowed_location_ids
    else:
        target_location_ids = allowed_location_ids

    # Get all products that have inventory in these locations
    product_locs = ProductLoc.query.filter(ProductLoc.location_id.in_(target_location_ids)).all()
    product_ids = list(set([pl.product_id for pl in product_locs]))

    products = Product.query.filter(Product.id.in_(product_ids)).all()

    product_list = [{
        'id': prod.id,
        'sku_id': prod.model_code,
        'product_name': prod.product_name,
        'category': prod.category,
        'brand': prod.brand
    } for prod in products]

    return jsonify(product_list)


# API: Get Forecast Data
@app.route('/api/forecast/data', methods=['GET'])
@login_required
def api_forecast_data():
    location_id = request.args.get('location_id')
    product_id = request.args.get('product_id')
    interval = request.args.get('interval', 'daily') # 'daily', 'weekly', 'biweekly', 'monthly'

    if not location_id or not product_id:
        return jsonify({'error': 'Location ID and Product ID are required'}), 400

    if current_user.role in ['Manager', 'Admin']:
        allowed_location_ids = [loc.id for loc in Location.query.all()]
    else:
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        allowed_location_ids = [ul.location_id for ul in user_locs]

    target_location_ids = allowed_location_ids
    if location_id != 'ALL':
        try:
            loc_id_int = int(location_id)
            if loc_id_int not in allowed_location_ids:
                return jsonify({'error': 'Unauthorized location'}), 403
            target_location_ids = [loc_id_int]
        except ValueError:
            target_location_ids = allowed_location_ids

    # Build base query for ProductLocs
    pl_query = ProductLoc.query.filter(ProductLoc.location_id.in_(target_location_ids))

    if product_id != 'ALL':
        try:
            prod_id_int = int(product_id)
            pl_query = pl_query.filter(ProductLoc.product_id == prod_id_int)
        except ValueError:
            pass

    product_locs = pl_query.all()
    if not product_locs:
        return jsonify({
            'chartData': [],
            'kpi': {},
            'alerts': [{'type': 'info', 'message': 'No data for this combination.'}]
        }) # No data for this combination

    pl_ids = [pl.id for pl in product_locs]
    current_stock = sum(pl.quantity_on_hand for pl in product_locs)

    # Fetch daily sales for the past 2 years (730 days) to allow for Monthly MAs
    today = datetime.now()
    start_date = today - timedelta(days=730)

    # Fetch actual sales from database
    sales_data = db.session.query(
        db.func.date(Sale.sale_date).label('date'),
        db.func.sum(SaleItem.quantity).label('total_quantity')
    ) \
    .join(SaleItem, SaleItem.sale_id == Sale.id) \
    .filter(SaleItem.pl_id.in_(pl_ids), Sale.sale_date >= start_date) \
    .group_by(db.func.date(Sale.sale_date)).all()

    sales_dict = {str(sale.date): sale.total_quantity for sale in sales_data}

    # First, generate a continuous daily series for the last 730 days
    daily_sales_raw = []
    for i in range(730, -1, -1):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        daily_vol = sales_dict.get(date_str, 0)
        daily_sales_raw.append({
            'date': target_date,
            'date_str': date_str,
            'raw_val': daily_vol
        })

    aggregated_data = []

    if interval == 'daily':
        for item in daily_sales_raw[-90:]: # Return last 90 days for daily view
            aggregated_data.append({
                'label': item['date_str'],
                'raw_val': item['raw_val']
            })
    elif interval == 'weekly':
        # Group into 7-day buckets, working backwards from today
        buckets = []
        current_bucket = []
        for item in reversed(daily_sales_raw):
            current_bucket.append(item)
            if len(current_bucket) == 7:
                buckets.append(current_bucket)
                current_bucket = []

        # Reverse buckets back to chronological order
        buckets.reverse()

        for bucket in buckets:
            # Re-reverse the bucket to get chronological order within the bucket for labeling
            bucket.reverse()
            total_vol = sum(x['raw_val'] for x in bucket)
            start_label = bucket[0]['date_str']
            end_label = bucket[-1]['date_str']
            aggregated_data.append({
                'label': f"{start_label} to {end_label}",
                'raw_val': total_vol
            })

    elif interval == 'biweekly':
        # Group into 14-day buckets
        buckets = []
        current_bucket = []
        for item in reversed(daily_sales_raw):
            current_bucket.append(item)
            if len(current_bucket) == 14:
                buckets.append(current_bucket)
                current_bucket = []

        buckets.reverse()
        for bucket in buckets:
            bucket.reverse()
            total_vol = sum(x['raw_val'] for x in bucket)
            start_label = bucket[0]['date_str']
            end_label = bucket[-1]['date_str']
            aggregated_data.append({
                'label': f"{start_label} to {end_label}",
                'raw_val': total_vol
            })

    elif interval == 'monthly':
        # Group by calendar month
        month_buckets = {}
        for item in daily_sales_raw:
            month_key = item['date'].strftime("%Y-%m")
            if month_key not in month_buckets:
                month_buckets[month_key] = 0
            month_buckets[month_key] += item['raw_val']

        # Ensure chronological order
        sorted_months = sorted(month_buckets.keys())
        for month in sorted_months:
            # Format to something like "Jan 2024"
            dt = datetime.strptime(month, "%Y-%m")
            label = dt.strftime("%b %Y")
            aggregated_data.append({
                'label': label,
                'raw_val': month_buckets[month]
            })

    # Calculate Moving Averages on aggregated data
    def calculate_ma(data, period):
        ma_data = []
        for i in range(len(data)):
            if i < period - 1:
                ma_data.append(None)
            else:
                window = [x['raw_val'] for x in data[i - period + 1 : i + 1]]
                ma_data.append(sum(window) / period)
        return ma_data

    ma3 = calculate_ma(aggregated_data, 3)
    ma7 = calculate_ma(aggregated_data, 7)
    ma14 = calculate_ma(aggregated_data, 14)

    chart_data = []

    # We might not want to show 730 days of data on the chart for daily.
    # Daily limits to 90 days. Weekly limits to ~24 weeks, etc.
    display_limit = 90
    if interval == 'weekly': display_limit = 26 # half year
    elif interval == 'biweekly': display_limit = 26 # year
    elif interval == 'monthly': display_limit = 24 # 2 years

    start_idx = max(0, len(aggregated_data) - display_limit)

    for i in range(start_idx, len(aggregated_data)):
        entry = {
            'date': aggregated_data[i]['label'],
            'volume': aggregated_data[i]['raw_val']
        }
        if ma3[i] is not None:
            entry['MA3'] = round(ma3[i], 2)
        if ma7[i] is not None:
            entry['MA7'] = round(ma7[i], 2)
        if ma14[i] is not None:
            entry['MA14'] = round(ma14[i], 2)

        chart_data.append(entry)

    # ---------------------------------------------------------
    # CALCULATE INDICATORS & ALERTS FOR THE LATEST PERIOD
    # ---------------------------------------------------------
    kpi = {}
    alerts = []

    if len(aggregated_data) > 0:
        latest_period = aggregated_data[-1]["raw_val"]
        prev_period = aggregated_data[-2]["raw_val"] if len(aggregated_data) > 1 else 0

        latest_ma3 = ma3[-1] if ma3[-1] is not None else 0
        latest_ma7 = ma7[-1] if ma7[-1] is not None else 0
        latest_ma14 = ma14[-1] if ma14[-1] is not None else 0

        # Trend Logic
        if latest_ma3 > latest_ma7:
            trend = "Uptrend"
        elif latest_ma3 < latest_ma7:
            trend = "Downtrend"
        else:
            trend = "Flat"

        # Demand Momentum = (CurrentPeriod - MA7) / MA7
        if latest_ma7 == 0:
            momentum = 0 if latest_period == 0 else None
        else:
            momentum = (latest_period - latest_ma7) / latest_ma7

        # Growth Rate = (CurrentPeriod - PreviousPeriod) / PreviousPeriod
        if prev_period == 0:
            growth_rate = 0 if latest_period == 0 else None
        else:
            growth_rate = (latest_period - prev_period) / prev_period

        # Rolling Sum (7-Period Total), Volatility, Range
        last_7 = [x["raw_val"] for x in aggregated_data[-7:]]
        rolling_sum = sum(last_7)

        if len(last_7) > 1:
            mean_7 = rolling_sum / len(last_7)
            variance = sum((x - mean_7) ** 2 for x in last_7) / (len(last_7) - 1)
            volatility = math.sqrt(variance)
        else:
            volatility = 0

        rng = max(last_7) - min(last_7) if last_7 else 0

        # Inventory Analytics
        if latest_ma7 == 0:
            stock_coverage = 0 if current_stock == 0 else None
        else:
            stock_coverage = current_stock / latest_ma7

        net_demand = latest_ma7 - current_stock
        remaining_stock = current_stock - latest_ma7

        kpi = {
            "MA3": round(latest_ma3, 2) if latest_ma3 is not None else None,
            "MA7": round(latest_ma7, 2) if latest_ma7 is not None else None,
            "MA14": round(latest_ma14, 2) if latest_ma14 is not None else None,
            "TrendLogic": trend,
            "DemandMomentum": round(momentum, 4) if momentum is not None else None,
            "GrowthRate": round(growth_rate, 4) if growth_rate is not None else None,
            "RollingSum7": rolling_sum,
            "Volatility": round(volatility, 2),
            "Range": rng,
            "StockCoverage": round(stock_coverage, 2) if stock_coverage is not None else None,
            "NetDemand": round(net_demand, 2) if net_demand is not None else None,
            "RemainingStock": round(remaining_stock, 2) if remaining_stock is not None else None,
            "CurrentStock": current_stock,
            "CurrentPeriod": latest_period
        }

        # Alerts
        # Trend Alert
        if len(ma3) > 1 and len(ma7) > 1:
            prev_ma3 = ma3[-2] if ma3[-2] is not None else 0
            prev_ma7 = ma7[-2] if ma7[-2] is not None else 0

            if latest_ma3 > latest_ma7 and prev_ma3 <= prev_ma7:
                alerts.append({"type": "info", "message": "Trend Alert: MA3 recently crossed above MA7 (Uptrend)."})
            elif latest_ma3 < latest_ma7 and prev_ma3 >= prev_ma7:
                alerts.append({"type": "warning", "message": "Trend Alert: MA3 recently crossed below MA7 (Downtrend)."})

        # Demand Spike
        if latest_period > (latest_ma7 * 1.5):
            alerts.append({"type": "info", "message": "Demand Spike: Current period demand is over 50% higher than MA7."})

        # Low Demand
        if latest_period < (latest_ma7 * 0.5):
            alerts.append({"type": "warning", "message": "Low Demand: Current period demand is less than 50% of MA7."})

        # Out of Stock Risk
        if current_stock < latest_ma7:
            alerts.append({"type": "error", "message": "Out of Stock Risk: Current stock is less than the 7-period moving average."})

        # Low Stock Warning
        if stock_coverage is not None and stock_coverage < 3:
            alerts.append({"type": "warning", "message": f"Low Stock Warning: Stock coverage is {round(stock_coverage, 1)} periods (less than 3)."})

        # Zero Activity
        if latest_period == 0:
            alerts.append({"type": "error", "message": "Zero Activity: No sales recorded for the current period."})

    return jsonify({
        "chartData": chart_data,
        "kpi": kpi,
        "alerts": alerts
    })

# API: Sales Endpoints
@app.route('/api/sales', methods=['GET', 'POST'])
@login_required
@role_required('Sales')
def api_sales():
    if request.method == 'GET':
        # Show all sales for the locations assigned to this user, plus sales made by this user
        user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
        loc_ids = [ul.location_id for ul in user_locs]

        if current_user.role == 'Admin' or current_user.role == 'Manager':
            sales = Sale.query.order_by(Sale.sale_date.desc()).all()
        else:
            sales = Sale.query.filter(
                (Sale.sold_by == current_user.id) | (Sale.location_id.in_(loc_ids))
            ).order_by(Sale.sale_date.desc()).all()

        return jsonify([{
            'id': sale.id,
            'customer_name': sale.customer_name,
            'client_email': sale.client_email,
            'status': sale.status,
            'total_amount': sale.total_amount,
            'sold_by': sale.sold_by,
            'location_id': sale.location_id,
            'date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
            'items': [{'pl_id': item.pl_id, 'product_name': item.product_loc.product.product_name, 'quantity': item.quantity, 'unit_price': item.unit_price} for item in sale.items]
        } for sale in sales])

    data = request.json
    pl_id = data.get('pl_id')
    quantity_sold = data.get('quantity_sold')
    customer_name = data.get('customer_name')
    client_email = data.get('client_email', f"{customer_name.replace(' ', '').lower()}@example.com" if customer_name else None)

    if not pl_id or not quantity_sold:
        return jsonify({'success': False, 'message': 'pl_id and quantity_sold are required'}), 400

    pl = ProductLoc.query.get(pl_id)
    if not pl:
        return jsonify({'success': False, 'message': 'Product Location not found'}), 404

    if pl.quantity_on_hand < int(quantity_sold):
        return jsonify({'success': False, 'message': 'Insufficient stock'}), 400

    unit_price = data.get('price', None)
    if unit_price is None or str(unit_price).strip() == '':
        unit_price = 100.0
        if pl.product.pricing:
            unit_price = pl.product.pricing[0].lsp_price or 100.0

    sale = Sale(
        location_id=pl.location_id,
        customer_name=customer_name,
        client_email=client_email,
        sold_by=current_user.id,
        status="Quoted",
        total_amount=float(unit_price) * int(quantity_sold)
    )
    try:
        db.session.add(sale)
        db.session.flush()

        sale_item = SaleItem(
            sale_id=sale.id,
            pl_id=pl.id,
            quantity=int(quantity_sold),
            unit_price=float(unit_price),
            subtotal=float(unit_price) * int(quantity_sold)
        )
        db.session.add(sale_item)
        db.session.commit()
        logger.info(f"Quote added successfully: PL ID {pl_id}, Qty {quantity_sold} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Quotation sent successfully!', 'sale_id': sale.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add Quote for PL ID {pl_id}: {str(e)}\n")
        return jsonify({'success': False, 'message': 'Database error occurred while creating Quote'}), 500

@app.route('/api/sales/dashboard', methods=['GET'])
@login_required
@role_required('Sales')
def api_sales_dashboard():
    user_locs = UserLocation.query.filter_by(uid=current_user.id).all()
    loc_ids = [ul.location_id for ul in user_locs]

    # Personal Sales (Verified or Paid, limited to assigned locations)
    personal_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.sold_by == current_user.id,
        Sale.location_id.in_(loc_ids),
        Sale.status.in_(['Verified', 'Paid'])
    ).scalar() or 0.0

    # Team Sales (Verified or Paid, across assigned locations)
    team_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.location_id.in_(loc_ids),
        Sale.status.in_(['Verified', 'Paid'])
    ).scalar() or 0.0

    # 1. Sales by Location (Bar Chart data)
    # Personal Sales, grouped by location.
    location_sales_raw = db.session.query(
        Location.description, db.func.sum(Sale.total_amount)
    ).join(Location, Sale.location_id == Location.id).filter(
        Sale.sold_by == current_user.id,
        Sale.location_id.in_(loc_ids),
        Sale.status.in_(['Verified', 'Paid'])
    ).group_by(Location.description).all()

    # The mockup uses short codes like "NY", "LDN". We can map common descriptions or use the first word/code.
    # To be safe, we'll just pass the description as the name, and the frontend can handle display.
    sales_by_location = [{'name': loc, 'value': amount} for loc, amount in location_sales_raw]

    # 2. Pipeline Velocity (Area Chart data)
    # Personal Sales grouped by month.
    # We will fetch all verified/paid personal sales and group them in Python by month.
    # Doing it in python is DB agnostic (avoids sqlite vs postgres strftime differences).
    from datetime import datetime
    all_personal_sales = Sale.query.filter(
        Sale.sold_by == current_user.id,
        Sale.location_id.in_(loc_ids),
        Sale.status.in_(['Verified', 'Paid'])
    ).all()

    # Group by YYYY-MM
    monthly_sales = {}
    for s in all_personal_sales:
        if s.sale_date:
            month_key = s.sale_date.strftime('%Y-%m') # e.g. "2023-10"
            monthly_sales[month_key] = monthly_sales.get(month_key, 0.0) + s.total_amount

    # Sort keys to ensure chronological order and format output
    # Mockup shows Jan, Feb, Mar etc. We'll pass the YYYY-MM and let frontend parse/format it,
    # or pass a 'month' string.
    pipeline_velocity = []
    for m_key in sorted(monthly_sales.keys()):
        # Parse back to get month name
        d = datetime.strptime(m_key, '%Y-%m')
        pipeline_velocity.append({
            'month': d.strftime('%b').upper(), # 'JAN', 'FEB'
            'full_date': m_key,
            'sales': monthly_sales[m_key]
        })

    return jsonify({
        'personalSales': personal_sales,
        'teamSales': team_sales,
        'salesByLocation': sales_by_location,
        'pipelineVelocity': pipeline_velocity
    })

@app.route('/api/sales/<int:sale_id>/status', methods=['PUT'])
@login_required
@role_required('Sales')
def api_update_sale_status(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({'success': False, 'message': 'Sale not found'}), 404

    data = request.json
    new_status = data.get('status')

    if new_status not in ['Quoted', 'Pending Verification', 'Verified', 'Paid']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    try:
        if new_status == 'Verified' and sale.status != 'Verified':
            # Deduct stock when verified
            for item in sale.items:
                if item.product_loc.quantity_on_hand < item.quantity:
                    return jsonify({'success': False, 'message': f'Insufficient stock for {item.product_loc.product.product_name}'}), 400
                item.product_loc.quantity_on_hand -= item.quantity

            # Create invoice automatically
            invoice_num = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{sale.id}"
            if not Invoice.query.filter_by(invoice_number=invoice_num).first():
                invoice = Invoice(
                    sale_id=sale.id,
                    invoice_number=invoice_num,
                    total_amount=sale.total_amount
                )
                db.session.add(invoice)

        sale.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'message': f'Sale status updated to {new_status}'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating sale status: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error updating status'}), 500

@app.route('/api/invoices', methods=['GET', 'POST'])
@login_required
@role_required('Sales')
def api_invoices():
    if request.method == 'GET':
        invoices = Invoice.query.order_by(Invoice.generated_date.desc()).all()
        return jsonify([{
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'total_amount': float(invoice.total_amount),
            'date': invoice.generated_date.strftime('%Y-%m-%d %H:%M:%S')
        } for invoice in invoices])

    data = request.json
    sale_id = data.get('sale_id')
    invoice_number = data.get('invoice_number')
    total_amount = data.get('total_amount')

    if not sale_id or not invoice_number or total_amount is None:
        return jsonify({'success': False, 'message': 'sale_id, invoice_number, and total_amount are required'}), 400

    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({'success': False, 'message': 'Sale not found'}), 404

    existing_invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
    if existing_invoice:
        return jsonify({'success': False, 'message': 'Invoice number already exists'}), 400

    invoice = Invoice(
        sale_id=sale_id,
        invoice_number=invoice_number,
        total_amount=float(total_amount)
    )
    try:
        db.session.add(invoice)
        db.session.commit()
        logger.info(f"Invoice generated successfully: Sale ID {sale_id}, Invoice Number {invoice_number} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Invoice generated successfully', 'invoice_id': invoice.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to generate Invoice for Sale ID {sale_id}: {str(e)}\n")
        return jsonify({'success': False, 'message': 'Database error occurred while generating Invoice'}), 500


# API: Assign Location (Manager Only)
@app.route('/api/assign-location', methods=['POST'])
@login_required
@role_required('Manager')
def api_assign_location():
    data = request.json
    uid = data.get('uid')
    location_id = data.get('location_id')

    if not uid or not location_id:
        return jsonify({'success': False, 'message': 'uid and location_id are required'}), 400

    user = User.query.get(uid)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    loc = Location.query.get(location_id)
    if not loc:
        return jsonify({'success': False, 'message': 'Location not found'}), 404

    existing_assignment = UserLocation.query.filter_by(uid=uid, location_id=location_id).first()
    if existing_assignment:
        return jsonify({'success': False, 'message': 'User is already assigned to this location'}), 400

    user_location = UserLocation(
        uid=uid,
        location_id=location_id
    )
    try:
        db.session.add(user_location)
        db.session.commit()
        logger.info(f"Location {location_id} assigned to user {uid} successfully by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Location assigned to user successfully', 'ul_id': user_location.ul_id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to assign Location {location_id} to User {uid}: {str(e)}\n")
        return jsonify({'success': False, 'message': 'Database error occurred while assigning Location'}), 500


# Serve React App for all other routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


# API: Get Workspace Team

@app.route('/api/users', methods=['POST'])
@login_required
@role_required('Admin')
def api_create_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([username, email, password, role]):
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password, role=role)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'User created successfully', 'user_id': new_user.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspace/team', methods=['GET'])
@login_required
def api_workspace_team():
    user = current_user
    user_locations = UserLocation.query.filter_by(uid=user.id).all()
    location_ids = [ul.location_id for ul in user_locations]

    if user.role in ['Manager', 'Admin']:
        if user.role == 'Admin':
            # Admin gets all users grouped by all locations
            locations = Location.query.all()
            location_ids = [l.id for l in locations]

        # Manager gets all members from all assigned locations, grouped by location
        team_data = []
        for loc_id in location_ids:
            loc = Location.query.get(loc_id)
            if loc:
                uls = UserLocation.query.filter_by(location_id=loc_id).all()
                members = []
                for ul in uls:
                    member_user = User.query.get(ul.uid)
                    if member_user:
                        members.append({
                            'id': member_user.id,
                            'username': member_user.username,
                            'email': member_user.email,
                            'role': member_user.role
                        })
                team_data.append({
                    'location_id': loc.id,
                    'location_name': loc.description,
                    'members': members
                })
        return jsonify({'success': True, 'team_grouped': team_data})
    else:
        # Non-manager gets a flat list of members in the same location(s)
        team_members_ids = set()
        for loc_id in location_ids:
            uls = UserLocation.query.filter_by(location_id=loc_id).all()
            for ul in uls:
                team_members_ids.add(ul.uid)

        members = []
        for uid in team_members_ids:
            member_user = User.query.get(uid)
            if member_user:
                members.append({
                    'id': member_user.id,
                    'username': member_user.username,
                    'email': member_user.email,
                    'role': member_user.role
                })
        return jsonify({'success': True, 'team': members})

# API: Workspace Users list for assignment Dropdown
@app.route('/api/workspace/users', methods=['GET'])
@login_required
@role_required('Manager')
def api_workspace_users():
    users = User.query.all()
    user_data = [{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role} for u in users]
    return jsonify({'success': True, 'users': user_data})

# API: Mail Endpoints
from models import InternalMail

@app.route('/api/workspace/mail/inbox', methods=['GET'])
@login_required
def api_mail_inbox():
    mails = InternalMail.query.filter_by(receiver_id=current_user.id).order_by(InternalMail.timestamp.desc()).all()
    mail_data = []
    for m in mails:
        sender = User.query.get(m.sender_id)
        mail_data.append({
            'id': m.id,
            'sender_name': sender.username if sender else 'Unknown',
            'sender_email': sender.email if sender else '',
            'subject': m.subject,
            'body': m.body,
            'timestamp': m.timestamp.isoformat(),
            'is_read': m.is_read
        })
    return jsonify({'success': True, 'mails': mail_data})

@app.route('/api/workspace/mail/sent', methods=['GET'])
@login_required
def api_mail_sent():
    mails = InternalMail.query.filter_by(sender_id=current_user.id).order_by(InternalMail.timestamp.desc()).all()
    mail_data = []
    for m in mails:
        receiver = User.query.get(m.receiver_id)
        mail_data.append({
            'id': m.id,
            'receiver_name': receiver.username if receiver else 'Unknown',
            'receiver_email': receiver.email if receiver else '',
            'subject': m.subject,
            'body': m.body,
            'timestamp': m.timestamp.isoformat(),
            'is_read': m.is_read
        })
    return jsonify({'success': True, 'mails': mail_data})

@app.route('/api/workspace/mail/send', methods=['POST'])
@login_required
def api_mail_send():
    data = request.json
    receiver_id = data.get('receiver_id')
    subject = data.get('subject')
    body = data.get('body')

    if not receiver_id or not subject or not body:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'success': False, 'message': 'Receiver not found'}), 404

    new_mail = InternalMail(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        subject=subject,
        body=body
    )
    db.session.add(new_mail)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Mail sent successfully'})

@app.route('/api/workspace/mail/<int:mail_id>/read', methods=['POST'])
@login_required
def api_mail_mark_read(mail_id):
    mail = InternalMail.query.get(mail_id)
    if not mail or mail.receiver_id != current_user.id:
        return jsonify({'success': False, 'message': 'Mail not found'}), 404

    mail.is_read = True
    db.session.commit()
    return jsonify({'success': True})


from sqlalchemy import func

@app.route('/api/warehouse/summary', methods=['GET'])
@login_required
def api_warehouse_summary():
    user_id = current_user.id
    location_id = request.args.get('location_id')

    if not location_id:
        return jsonify({'success': False, 'message': 'Location ID is required'}), 400

    ul = UserLocation.query.filter_by(uid=user_id, location_id=location_id).first()
    if not ul and current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized access to location'}), 403

    location = Location.query.get(location_id)
    if not location:
        return jsonify({'success': False, 'message': 'Location not found'}), 404

    location_ul_ids = [ul_item.ul_id for ul_item in UserLocation.query.filter_by(location_id=location_id).all()]
    if not location_ul_ids:
        location_ul_ids = [0]

    try:
        # 1. Total Sales (Amount)
        total_sales = db.session.query(func.sum(Sale.total_amount)).filter_by(location_id=location_id).scalar() or 0.0

        # 2. Total Items Sold
        total_items_sold = db.session.query(func.sum(SaleItem.quantity)).join(Sale).filter(Sale.location_id == location_id).scalar() or 0

        # 3. Total Stock (across all products at this location)
        product_locs = ProductLoc.query.filter_by(location_id=location_id).all()
        total_stock = sum([pl.quantity_on_hand for pl in product_locs])

        # 4. Stock by Category
        stock_by_category_dict = {}
        for pl in product_locs:
            product = Product.query.get(pl.product_id)
            if product:
                cat = product.category or 'Uncategorized'
                stock_by_category_dict[cat] = stock_by_category_dict.get(cat, 0) + pl.quantity_on_hand

        stock_by_category = [{"category": k, "stock": v} for k, v in stock_by_category_dict.items()]

        # 5. Products available in this location
        products_list = []
        for pl in product_locs:
            product = Product.query.get(pl.product_id)
            if product:
                incoming = ProductOrder.query.join(ProductVendor).filter(ProductVendor.product_id == product.id, ProductOrder.ul_id.in_(location_ul_ids)).filter(ProductOrder.status.in_(['Pending', 'Processing', 'Ordered', 'Shipped'])).with_entities(func.sum(ProductOrder.order_qty)).scalar() or 0
                products_list.append({
                    "id": product.id,
                    "sku": product.model_code,
                    "name": product.product_name,
                    "category": product.category,
                    "current_stock": pl.quantity_on_hand,
                    "incoming_stock": int(incoming)
                })

        return jsonify({
            'success': True,
            'location': {
                'id': location.id,
                'loc_code': location.loc_code,
                'description': location.description
            },
            'data': {
                'total_sales': float(total_sales),
                'total_items_sold': total_items_sold,
                'total_stock': total_stock,
                'stock_by_category': stock_by_category,
                'products': products_list
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/warehouse/product_stats', methods=['GET'])
@login_required
def api_warehouse_product_stats():
    user_id = current_user.id
    location_id = request.args.get('location_id')
    product_id = request.args.get('product_id')

    if not location_id or not product_id:
        return jsonify({'success': False, 'message': 'Location ID and Product ID are required'}), 400

    ul = UserLocation.query.filter_by(uid=user_id, location_id=location_id).first()
    if not ul and current_user.role != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized access to location'}), 403

    location_ul_ids = [ul_item.ul_id for ul_item in UserLocation.query.filter_by(location_id=location_id).all()]
    if not location_ul_ids:
        location_ul_ids = [0]

    location = Location.query.get(location_id)
    product = Product.query.get(product_id)

    if not location or not product:
        return jsonify({'success': False, 'message': 'Location or Product not found'}), 404

    try:
        # Current stock at this location
        pl = ProductLoc.query.filter_by(product_id=product_id, location_id=location_id).first()
        current_stock = pl.quantity_on_hand if pl else 0

        # Incoming stock at this location
        incoming = ProductOrder.query.join(ProductVendor).filter(ProductVendor.product_id == product_id, ProductOrder.ul_id.in_(location_ul_ids)).filter(ProductOrder.status.in_(['Pending', 'Processing', 'Ordered', 'Shipped'])).with_entities(func.sum(ProductOrder.order_qty)).scalar() or 0

        reserved = 0 # Can be implemented based on pending sales or allocations

        # Sales history (last 30 days) at this location
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        sales_data = db.session.query(
            func.date(Sale.sale_date).label('date'),
            func.sum(SaleItem.quantity).label('total_qty')
        ).join(SaleItem, SaleItem.sale_id == Sale.id).join(ProductLoc, SaleItem.pl_id == ProductLoc.id).filter(
            Sale.location_id == location_id,
            ProductLoc.product_id == product_id,
            Sale.sale_date >= thirty_days_ago
        ).group_by(func.date(Sale.sale_date)).order_by(func.date(Sale.sale_date)).all()

        sales_history = []
        date_dict = {str(item.date): int(item.total_qty) for item in sales_data}

        # Fill in zero days
        total_30d_sales = 0
        for i in range(30, -1, -1):
            d = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            qty = date_dict.get(d, 0)
            sales_history.append({"date": d, "sales": qty})
            total_30d_sales += qty

        avg_daily_sales = total_30d_sales / 30.0

        # Recent activity
        activities = []

        # Recent sales
        recent_sales = db.session.query(Sale).join(SaleItem, SaleItem.sale_id == Sale.id).join(ProductLoc, SaleItem.pl_id == ProductLoc.id).filter(
            Sale.location_id == location_id,
            ProductLoc.product_id == product_id
        ).order_by(Sale.sale_date.desc()).limit(3).all()

        for sale in recent_sales:
            for item in sale.items:
                pl_item = ProductLoc.query.get(item.pl_id)
                if pl_item and str(pl_item.product_id) == str(product_id):
                    activities.append({
                        "date": sale.sale_date.strftime('%Y-%m-%d'),
                        "description": f"Sold {item.quantity} units",
                        "type": "SALE",
                        "timestamp": sale.sale_date
                    })

        # Recent POs
        recent_pos = ProductOrder.query.join(ProductVendor).filter(
            ProductOrder.ul_id.in_(location_ul_ids),
            ProductVendor.product_id == product_id
        ).order_by(ProductOrder.created_at.desc()).limit(3).all()

        for po in recent_pos:
            status_type = "RESTOCK" if po.status in ["Delivered", "Received"] else "ORDER"
            activities.append({
                "date": (po.ets_date.strftime('%Y-%m-%d') if po.ets_date else po.created_at.strftime('%Y-%m-%d')),
                "description": f"PO {po.po_reference} ({po.status}): {po.order_qty} units",
                "type": status_type,
                "timestamp": po.ets_date or po.created_at or datetime.utcnow()
            })

        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        for a in activities:
            del a["timestamp"]

        return jsonify({
            'success': True,
            'location': {
                'id': location.id,
                'loc_code': location.loc_code,
                'description': location.description
            },
            'data': {
                'id': product.id,
                'sku': product.model_code,
                'name': product.product_name,
                'category': product.category,
                'brand': product.brand,
                'status': product.status,
                'current_stock': current_stock,
                'incoming_stock': int(incoming),
                'reserved_stock': reserved,
                'avg_daily_sales': avg_daily_sales,
                'sales_history': sales_history,
                'recent_activities': activities[:5]
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Internal server error'}), 500



if __name__ == '__main__':
    # No db.create_all() here, relying on seed script
    app.run(debug=True)
