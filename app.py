import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from functools import wraps
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

# Role-based access control decorator
def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Unauthorized'}), 401
            if current_user.role != role_name and current_user.role != 'Admin':
                return jsonify({'error': 'Forbidden - Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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

    return jsonify({'success': True, 'role': user.role, 'username': user.username})

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

# API: Get Current User's Assigned Locations
@app.route('/api/my-locations', methods=['GET'])
@login_required
def api_my_locations():
    # Admins can see all, or we just return the ones explicitly assigned
    user_locations = UserLocation.query.filter_by(user_id=current_user.id).all()
    locations = []
    for ul in user_locations:
        loc = Location.query.get(ul.location_id)
        if loc:
            locations.append({
                'ul_id': ul.id,
                'location_id': loc.id,
                'location_name': loc.description,
                'loc_code': loc.loc_code
            })
    return jsonify(locations)

# API: Generate PR (Product Order)
@app.route('/api/generate-pr', methods=['POST'])
@login_required
@role_required('Warehouse')
def api_generate_pr():
    data = request.json

    # User must provide a specific user_location ID (ul_id) that they want to order for
    ul_id = data.get('ul_id')
    if not ul_id:
        return jsonify({'success': False, 'message': 'User Location ID (ul_id) is required. Please select a location.'}), 400

    # Verify the user actually has this user_location
    user_loc = UserLocation.query.filter_by(id=ul_id, user_id=current_user.id).first()
    if not user_loc:
        return jsonify({'success': False, 'message': 'You are not assigned to the selected location.'}), 403

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

        pr = ProductOrder(
            pv_id=pv.id,
            ul_id=user_loc.id,
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

# API: Assign Location
@app.route('/api/assign-location', methods=['POST'])
@login_required
@role_required('Manager')
def api_assign_location():
    data = request.json
    user_id = data.get('user_id')
    location_id = data.get('location_id')

    if not user_id or not location_id:
        return jsonify({'success': False, 'message': 'User ID and Location ID are required'}), 400

    existing_assignment = UserLocation.query.filter_by(user_id=user_id, location_id=location_id).first()
    if existing_assignment:
        return jsonify({'success': False, 'message': 'User is already assigned to this location'}), 400

    new_assignment = UserLocation(user_id=user_id, location_id=location_id)
    db.session.add(new_assignment)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Location assigned successfully', 'id': new_assignment.id})

# API: Get All Locations (For Managers assigning)
@app.route('/api/all-locations', methods=['GET'])
@login_required
@role_required('Manager')
def api_all_locations():
    locations = Location.query.all()
    loc_list = [{'id': l.id, 'description': l.description, 'loc_code': l.loc_code} for l in locations]
    return jsonify(loc_list)

# API: Get All Users (For Managers assigning)
@app.route('/api/all-users', methods=['GET'])
@login_required
@role_required('Manager')
def api_all_users():
    users = User.query.all()
    user_list = [{'id': u.id, 'username': u.username, 'role': u.role} for u in users]
    return jsonify(user_list)

# API: Add Sale
@app.route('/api/sales', methods=['POST'])
@login_required
@role_required('Sales')
def api_add_sale():
    data = request.json
    product_id = data.get('product_id')
    location_id = data.get('location_id')
    quantity = data.get('quantity')
    customer_name = data.get('customer_name')

    if not all([product_id, location_id, quantity]):
        return jsonify({'success': False, 'message': 'Product ID, Location ID, and Quantity are required'}), 400

    # Find the ProductLoc
    pl = ProductLoc.query.filter_by(product_id=product_id, location_id=location_id).first()
    if not pl:
        return jsonify({'success': False, 'message': 'Product not found at the specified location'}), 400

    if pl.quantity_on_hand < int(quantity):
        return jsonify({'success': False, 'message': 'Insufficient stock at the specified location'}), 400

    # Deduct stock
    pl.quantity_on_hand -= int(quantity)

    new_sale = Sale(
        pl_id=pl.id,
        quantity_sold=int(quantity),
        customer_name=customer_name,
        sold_by=current_user.id
    )
    db.session.add(new_sale)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Sale added successfully', 'id': new_sale.id})

# API: Generate Invoice
@app.route('/api/invoices', methods=['POST'])
@login_required
@role_required('Sales')
def api_generate_invoice():
    data = request.json
    sale_id = data.get('sale_id')

    if not sale_id:
        return jsonify({'success': False, 'message': 'Sale ID is required'}), 400

    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({'success': False, 'message': 'Sale not found'}), 404

    # Check if invoice already exists
    if sale.invoice:
        return jsonify({'success': False, 'message': 'Invoice already exists for this sale'}), 400

    # Calculate total amount (mock logic assuming LSP price)
    pricing = Pricing.query.filter_by(product_id=sale.product_loc.product_id).first()
    price = pricing.lsp_price if pricing else 100 # Fallback
    total_amount = sale.quantity_sold * price

    new_invoice = Invoice(
        sale_id=sale.id,
        invoice_number=f"INV-{datetime.utcnow().strftime('%Y')}-{sale.id + 10000}",
        total_amount=total_amount
    )
    db.session.add(new_invoice)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Invoice generated successfully', 'invoice_number': new_invoice.invoice_number})

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
