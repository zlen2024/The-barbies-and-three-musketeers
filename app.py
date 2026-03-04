import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from functools import wraps
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Location, ProductLoc, Vendor, ProductVendor, ProductOrder, Pricing, Campaign, Sale, Forecast, UserLocation, Invoice

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

    # Try matching username first
    user = User.query.filter_by(username=username_or_email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    login_user(user)
    # user.last_login = datetime.utcnow() # User model doesn't have last_login anymore in new schema
    # db.session.commit()

    return jsonify({'success': True, 'role': user.role, 'username': user.username, 'user_id': user.id})

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
    total_sales_units = db.session.query(db.func.sum(Sale.quantity_sold)).scalar() or 0

    # Estimate Revenue: Get all sales, and for each, find the product's price.
    # This is heavy for production but fine for demo.
    # Better: SQL Query
    # SELECT SUM(s.quantity_sold * p.lsp_price) FROM sale s
    # JOIN product_loc pl ON s.pl_id = pl.pl_id
    # JOIN product pr ON pl.product_id = pr.product_id
    # JOIN pricing p ON pr.product_id = p.product_id

    total_revenue = 0
    sales = Sale.query.all()
    # Cache pricing
    pricings = {p.product_id: p.lsp_price for p in Pricing.query.all()}

    for sale in sales:
        prod_id = sale.product_loc.product_id
        price = pricings.get(prod_id, 0)
        total_revenue += sale.quantity_sold * price

    # 2. Predicted Demand
    total_predicted_demand = db.session.query(db.func.sum(Forecast.projected_demand)).scalar() or 0

    # 3. Chart Data (Sales by Month)
    # Group by YYYY-MM
    # SQLite strftime is %Y-%m

    # We need to aggregate sales by month for the last 6 months
    today = datetime.now() # Use now() instead of utcnow()
    chart_data = []

    for i in range(5, -1, -1):
        # Calculate start and end of the month
        # Logic: Go back i months.
        # This is a bit rough for days, let's just pick month names.

        target_month_date = today - timedelta(days=30*i)
        month_str = target_month_date.strftime("%b")
        month_num = target_month_date.strftime("%m")
        year_num = target_month_date.strftime("%Y")

        # Query sales for this month
        # SQLite specific date string matching or range
        # Let's filter by range

        # Start of month
        start_date = datetime(int(year_num), int(month_num), 1)
        # End of month (start of next month)
        if int(month_num) == 12:
            end_date = datetime(int(year_num) + 1, 1, 1)
        else:
            end_date = datetime(int(year_num), int(month_num) + 1, 1)

        actual_sales = db.session.query(db.func.sum(Sale.quantity_sold)).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date < end_date
        ).scalar() or 0

        # Mock Prediction (slightly different from actual)
        prediction = int(actual_sales * 1.05) + 50

        chart_data.append({
            "date": month_str,
            "Actual Sales": actual_sales,
            "AI Prediction": prediction
        })

    # 4. Product Count
    product_count = Product.query.count()

    data = {
        'totalSales': total_revenue, # Sending Value
        'predictedDemand': total_predicted_demand,
        'accuracy': "92.5%", # Mock
        'chartData': chart_data,
        'smartWhy': "Inventory turnover is optimal in Main Warehouse, but Online Channels are showing a 15% stockout risk for high-velocity items. Recommend rebalancing stock to channels.",
        'productCount': product_count
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
        db.session.add(pr)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Purchase Request created for {product.model_code}'})

    return jsonify({'success': False, 'message': 'Product not found'}), 404

# API: Inventory List
@app.route('/api/inventory', methods=['GET'])
@login_required
def api_inventory():
    products = Product.query.all()
    inventory_list = []

    for product in products:
        # Calculate AMS (3-Month)
        cutoff_3m = datetime.now() - timedelta(days=90)
        total_sales_3m = db.session.query(db.func.sum(Sale.quantity_sold)).join(ProductLoc).filter(
            ProductLoc.product_id == product.id,
            Sale.sale_date >= cutoff_3m
        ).scalar() or 0
        ams_3m = round(total_sales_3m / 3, 1)

        # Status Logic
        stock = product.total_stock
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
    db.session.add(new_product)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Product added successfully', 'id': new_product.id})

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
    db.session.add(new_vendor)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Vendor added successfully', 'id': new_vendor.id})

# API: Product Detail
@app.route('/api/inventory/products/<path:sku>', methods=['GET'])
@login_required
def api_product_detail(sku):
    # sku here is model_code
    product = Product.query.filter_by(model_code=sku).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Calculate AMS
    cutoff_3m = datetime.now() - timedelta(days=90)
    total_sales_3m = db.session.query(db.func.sum(Sale.quantity_sold)).join(ProductLoc).filter(
        ProductLoc.product_id == product.id,
        Sale.sale_date >= cutoff_3m
    ).scalar() or 0
    ams_3m = round(total_sales_3m / 3, 1)

    cutoff_6m = datetime.now() - timedelta(days=180)
    total_sales_6m = db.session.query(db.func.sum(Sale.quantity_sold)).join(ProductLoc).filter(
        ProductLoc.product_id == product.id,
        Sale.sale_date >= cutoff_6m
    ).scalar() or 0
    ams_6m = round(total_sales_6m / 6, 1)

    # Calculate Trend
    trend_percentage = 0
    if ams_6m > 0:
        trend_percentage = round(((ams_3m - ams_6m) / ams_6m) * 100, 1)

    # Coverage
    coverage = 0
    if ams_3m > 0:
        coverage = round(product.total_stock / ams_3m, 1)

    # Sales Channel Distribution
    sales_channels = db.session.query(
        Location.description,
        db.func.sum(Sale.quantity_sold)
    ).join(ProductLoc, ProductLoc.location_id == Location.id).join(Sale, Sale.pl_id == ProductLoc.id).filter(
        ProductLoc.product_id == product.id
    ).group_by(Location.description).all()

    distribution_data = [{'name': channel, 'value': quantity} for channel, quantity in sales_channels]

    # Sales Trend (Line Chart) - Last 6 months
    sales_trend = []
    today = datetime.now()
    for i in range(5, -1, -1):
        month_start = (today - timedelta(days=30*i)).replace(day=1)
        if today.month == 12 and i == 0:
             month_end = datetime(today.year + 1, 1, 1)
        elif i == 0:
             # Logic for current month end is tricky without dateutil, so let's just go to next month start of today
             # Assuming today is safe
             if today.month == 12:
                 month_end = datetime(today.year + 1, 1, 1)
             else:
                 month_end = datetime(today.year, today.month + 1, 1)
        else:
             month_end = month_start + timedelta(days=30) # Rough approx

        monthly_sales = db.session.query(db.func.sum(Sale.quantity_sold)).join(ProductLoc).filter(
            ProductLoc.product_id == product.id,
            Sale.sale_date >= month_start,
            Sale.sale_date < month_end
        ).scalar() or 0

        sales_trend.append({
            'date': month_start.strftime("%b"),
            'Actual Sales': monthly_sales,
            'Forecast': monthly_sales * 1.1
        })

    # Purchase Orders
    orders = db.session.query(ProductOrder).join(ProductVendor).filter(
        ProductVendor.product_id == product.id
    ).order_by(ProductOrder.created_at.desc()).all()

    # Calculate Avg Lead Time
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

    # Location Breakdown
    location_stock = [{
        'location': pl.location.description,
        'type': pl.location.type,
        'quantity': pl.quantity_on_hand
    } for pl in product.product_locs]

    # Vendors
    vendor_info = [{
        'id': pv.vendor_id,
        'name': pv.vendor.vendor_name,
        'cost': pv.cost_price,
        'lead_time': pv.lead_time_days
    } for pv in product.product_vendors]

    # Pricing
    pricing_info = {}
    if product.pricing:
        p = product.pricing[0]
        pricing_info = {
            'lsp': p.lsp_price,
            'wm': p.wm_price,
            'em': p.em_price
        }

    # Incoming Stock
    total_incoming = sum([o.order_qty for o in orders if o.status == 'Ordered'])

    data = {
        'product': {
            'name': product.product_name,
            'sku': product.model_code,
            'category': product.category,
            'status': "In Stock" if product.total_stock > 0 else "Critical",
            'lead_time': int(avg_lead_time)
        },
        'stock_health': {
            'total_physical': product.total_stock,
            'reserved': 0,
            'free_to_sell': product.total_stock
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
            'rationale': product.forecast.smart_why_rationale if product.forecast else "No forecast available."
        },
        'locations': location_stock,
        'vendors': vendor_info,
        'pricing': pricing_info
    }

    return jsonify(data)

# API: Get Locations for Product (for inventory expanded row)
@app.route('/api/inventory/<int:product_id>/locations', methods=['GET'])
@login_required
def api_product_locations(product_id):
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
    orders = ProductOrder.query.order_by(ProductOrder.created_at.desc()).all()

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
@app.route('/api/orders/<int:order_id>/confirm', methods=['POST'])
@login_required
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

    db.session.commit()
    return jsonify({'success': True, 'message': 'Order confirmed successfully'})

# API: Get Locations
@app.route('/api/forecast/locations', methods=['GET'])
@login_required
def api_forecast_locations():
    locations = Location.query.all()
    location_list = [{
        'id': loc.id,
        'loc_code': loc.loc_code,
        'description': loc.description,
        'type': loc.type
    } for loc in locations]
    return jsonify(location_list)

# API: Get Products for Location
@app.route('/api/forecast/products', methods=['GET'])
@login_required
def api_forecast_products():
    location_id = request.args.get('location_id')
    if not location_id:
        return jsonify({'error': 'Location ID is required'}), 400

    # Get all products that have inventory in this location
    product_locs = ProductLoc.query.filter_by(location_id=location_id).all()
    product_ids = [pl.product_id for pl in product_locs]

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

    if not location_id or not product_id:
        return jsonify({'error': 'Location ID and Product ID are required'}), 400

    # Get the specific ProductLoc ID for this location and product
    product_loc = ProductLoc.query.filter_by(location_id=location_id, product_id=product_id).first()

    if not product_loc:
        return jsonify([]) # No data for this combination

    # Fetch daily sales for this product_loc for the past 90 days
    today = datetime.now()
    start_date = today - timedelta(days=90)

    # Simple mock data generation based on actual data if available, or just mock it for visual purposes if no actual sales
    # The current DB seed might not have daily sales, only aggregated or a few entries. Let's mock a rich daily dataset.

    import random

    # We will generate mock data for 90 days.
    # In a real app, you would query:
    # sales = db.session.query(db.func.date(Sale.sale_date), db.func.sum(Sale.quantity_sold)) \
    #            .filter(Sale.pl_id == product_loc.id, Sale.sale_date >= start_date) \
    #            .group_by(db.func.date(Sale.sale_date)).all()

    chart_data = []
    base_sales = random.randint(10, 50)

    daily_sales_raw = []

    for i in range(90, -1, -1):
        target_date = today - timedelta(days=i)

        # Add some random walk to sales to make it look like a real chart
        change = random.randint(-5, 6)
        base_sales = max(0, base_sales + change)

        # Add weekly seasonality (lower on weekends)
        if target_date.weekday() >= 5:
            daily_vol = max(0, int(base_sales * 0.5))
        else:
            daily_vol = base_sales

        daily_sales_raw.append({
            'date': target_date.strftime("%Y-%m-%d"),
            'volume': daily_vol,
            'raw_val': daily_vol
        })

    # Calculate Moving Averages
    def calculate_ma(data, period):
        ma_data = []
        for i in range(len(data)):
            if i < period - 1:
                ma_data.append(None)
            else:
                window = [x['raw_val'] for x in data[i - period + 1 : i + 1]]
                ma_data.append(sum(window) / period)
        return ma_data

    ma3 = calculate_ma(daily_sales_raw, 3)
    ma7 = calculate_ma(daily_sales_raw, 7)
    ma14 = calculate_ma(daily_sales_raw, 14)

    for i in range(len(daily_sales_raw)):
        entry = {
            'date': daily_sales_raw[i]['date'],
            'volume': daily_sales_raw[i]['volume']
        }
        if ma3[i] is not None:
            entry['MA3'] = round(ma3[i], 2)
        if ma7[i] is not None:
            entry['MA7'] = round(ma7[i], 2)
        if ma14[i] is not None:
            entry['MA14'] = round(ma14[i], 2)

        chart_data.append(entry)

    return jsonify(chart_data)

# API: Sales Endpoints
@app.route('/api/sales', methods=['GET', 'POST'])
@login_required
@role_required('Sales')
def api_sales():
    if request.method == 'GET':
        sales = Sale.query.order_by(Sale.sale_date.desc()).all()
        return jsonify([{
            'id': sale.id,
            'customer_name': sale.customer_name,
            'quantity': sale.quantity_sold,
            'date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S')
        } for sale in sales])

    data = request.json
    pl_id = data.get('pl_id')
    quantity_sold = data.get('quantity_sold')
    customer_name = data.get('customer_name')

    if not pl_id or not quantity_sold:
        return jsonify({'success': False, 'message': 'pl_id and quantity_sold are required'}), 400

    pl = ProductLoc.query.get(pl_id)
    if not pl:
        return jsonify({'success': False, 'message': 'Product Location not found'}), 404

    if pl.quantity_on_hand < int(quantity_sold):
        return jsonify({'success': False, 'message': 'Insufficient stock'}), 400

    # Deduct stock
    pl.quantity_on_hand -= int(quantity_sold)

    sale = Sale(
        pl_id=pl_id,
        quantity_sold=int(quantity_sold),
        customer_name=customer_name,
        sold_by=current_user.id
    )
    db.session.add(sale)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Sale added successfully', 'sale_id': sale.id})


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
    db.session.add(invoice)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Invoice generated successfully', 'invoice_id': invoice.id})


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
    db.session.add(user_location)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Location assigned to user successfully', 'ul_id': user_location.ul_id})


# Serve React App for all other routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # No db.create_all() here, relying on seed script
    app.run(debug=True)
