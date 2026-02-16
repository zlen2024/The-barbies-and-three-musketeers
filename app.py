import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Inventory, Forecast, HistoricalSales, PurchaseRequest, Vendor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key' # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 1. Authentication Route
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('login.html')

# 2. Main Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.all()
    return render_template('dashboard.html', products=products)

# 3. Intelligent Forecasting & Reasoning Route
@app.route('/forecast/<sku_id>')
@login_required
def forecast(sku_id):
    product = Product.query.filter_by(sku_id=sku_id).first_or_404()
    return render_template('forecasting.html', product=product)

# 4. Purchase Request (PR) Generation Route
@app.route('/generate-pr', methods=['GET', 'POST'])
@login_required
def generate_pr():
    sku_id = request.args.get('sku_id')
    product = None
    if sku_id:
        product = Product.query.filter_by(sku_id=sku_id).first()

    if request.method == 'POST':
        sku_id_form = request.form.get('sku_id')
        quantity = request.form.get('quantity')

        product = Product.query.filter_by(sku_id=sku_id_form).first()
        if product and quantity:
            pr = PurchaseRequest(
                sku_id_fk=product.id,
                requested_quantity=int(quantity),
                status='Pending',
                created_by=current_user.id
            )
            db.session.add(pr)
            db.session.commit()
            flash('Purchase Request created successfully!')
            return redirect(url_for('dashboard'))

    return render_template('pr_generator.html', product=product)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
