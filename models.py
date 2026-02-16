from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# 1. User & Authentication Table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'Procurement' or 'Sales'
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

# Association Table for Vendor <-> Product (SKU)
vendor_sku = db.Table('vendor_sku',
    db.Column('vendor_id', db.Integer, db.ForeignKey('vendor.id'), primary_key=True),
    db.Column('sku_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

# 2. Master Product (SKU) Table
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku_id = db.Column(db.String(50), unique=True, nullable=False) # The actual SKU string e.g., 'SKU-123'
    product_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    unit_price = db.Column(db.Float)
    lead_time = db.Column(db.Integer) # in days
    minimum_stock_level = db.Column(db.Integer)

    @property
    def current_stock(self):
        return self.inventory.total_stock_on_hand if self.inventory else 0

    @property
    def stock_status(self):
        if not self.inventory:
            return 'Unknown'
        stock = self.inventory.total_stock_on_hand
        min_stock = self.minimum_stock_level

        if stock <= min_stock * 0.3:
            return 'Critical'
        elif stock <= min_stock:
            return 'Low Stock'
        else:
            return 'In Stock'

    # Relationships
    inventory = db.relationship('Inventory', backref='product', uselist=False, cascade="all, delete-orphan")
    sales_history = db.relationship('HistoricalSales', backref='product', lazy=True)
    forecast = db.relationship('Forecast', backref='product', uselist=False, cascade="all, delete-orphan")
    purchase_requests = db.relationship('PurchaseRequest', backref='product', lazy=True)
    vendors = db.relationship('Vendor', secondary=vendor_sku, backref=db.backref('products', lazy='dynamic'))

    def __repr__(self):
        return f'<Product {self.sku_id}>'

# 3. Inventory & Stock Movement Table
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku_id_fk = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, unique=True)
    total_stock_on_hand = db.Column(db.Integer, default=0)
    incoming_stock = db.Column(db.Integer, default=0)
    stock_aging_days = db.Column(db.Integer, default=0)
    last_updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Inventory for SKU {self.sku_id_fk}>'

# 4. Historical Sales Data Table
class HistoricalSales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku_id_fk = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    sales_channel = db.Column(db.String(100)) # e.g., Lazada, Shopee, E-store
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Sales {self.id} - SKU {self.sku_id_fk}>'

# 5. Forecast & Reasoning Table
class Forecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku_id_fk = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, unique=True)
    projected_demand = db.Column(db.Integer)
    confidence_score = db.Column(db.Float)
    smart_why_rationale = db.Column(db.Text) # LLM-generated explanation

    def __repr__(self):
        return f'<Forecast for SKU {self.sku_id_fk}>'

# 6. Purchase Request (PR) Table
class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku_id_fk = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    requested_quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='purchase_requests')

    def __repr__(self):
        return f'<PR {self.id} - Status {self.status}>'

# 7. Vendor/Supplier Table
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(120))

    def __repr__(self):
        return f'<Vendor {self.vendor_name}>'
