import os
from datetime import datetime
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
