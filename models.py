from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# 1. Users Table
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'Admin', 'Warehouse', 'Sales', 'Manager'
    password_hash = db.Column(db.String(200), nullable=False)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'

# 2. Core Data (Products & Locations)
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column('product_id', db.Integer, primary_key=True)
    model_code = db.Column(db.String(100), unique=True, nullable=False) # e.g., HT-PLATZ-450-H
    category = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    status = db.Column(db.String(50)) # Active/Discontinued
    product_name = db.Column(db.String(200)) # Added for display convenience if needed, or map from model_code

    # Relationships
    product_locs = db.relationship('ProductLoc', backref='product', lazy=True)
    product_vendors = db.relationship('ProductVendor', backref='product', lazy=True)
    pricing = db.relationship('Pricing', backref='product', lazy=True)

    @property
    def total_stock(self):
        return sum(pl.quantity_on_hand for pl in self.product_locs)

    def __repr__(self):
        return f'<Product {self.model_code}>'

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column('location_id', db.Integer, primary_key=True)
    loc_code = db.Column(db.String(50), unique=True, nullable=False) # e.g., BR-NM1
    description = db.Column(db.String(200))
    type = db.Column(db.String(50)) # 'Physical Warehouse' or 'Online Channel'

    # Relationships
    product_locs = db.relationship('ProductLoc', backref='location', lazy=True)
    user_locations = db.relationship('UserLocation', backref='location', lazy=True)

    def __repr__(self):
        return f'<Location {self.loc_code}>'

class UserLocation(db.Model):
    __tablename__ = 'user_location'
    ul_id = db.Column('ul_id', db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.location_id'), nullable=False)

    # Relationships
    user = db.relationship('User', backref='user_locations', lazy=True)

    def __repr__(self):
        return f'<UserLocation U:{self.uid} L:{self.location_id}>'

class ProductLoc(db.Model):
    __tablename__ = 'product_loc'
    id = db.Column('pl_id', db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.location_id'), nullable=False)
    quantity_on_hand = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    # Relationship to sales
    sales = db.relationship('Sale', backref='product_loc', lazy=True)

    def __repr__(self):
        return f'<ProductLoc P:{self.product_id} L:{self.location_id} Q:{self.quantity_on_hand}>'

# 3. Supply Chain (Vendors & Ordering)
class Vendor(db.Model):
    __tablename__ = 'vendor'
    id = db.Column('vendor_id', db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    phone_number = db.Column(db.String(50))
    is_overseas = db.Column(db.Boolean, default=False)

    product_vendors = db.relationship('ProductVendor', backref='vendor', lazy=True)

    def __repr__(self):
        return f'<Vendor {self.vendor_name}>'

class ProductVendor(db.Model):
    __tablename__ = 'product_vendor'
    id = db.Column('pv_id', db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.vendor_id'), nullable=False)
    cost_price = db.Column(db.Float)
    lead_time_days = db.Column(db.Integer)

    # Relationships
    orders = db.relationship('ProductOrder', backref='product_vendor', lazy=True)

    def __repr__(self):
        return f'<ProductVendor P:{self.product_id} V:{self.vendor_id}>'

class ProductOrder(db.Model):
    __tablename__ = 'product_order'
    id = db.Column('order_id', db.Integer, primary_key=True)
    pv_id = db.Column(db.Integer, db.ForeignKey('product_vendor.pv_id'), nullable=False)
    ul_id = db.Column(db.Integer, db.ForeignKey('user_location.ul_id'), nullable=False)
    po_reference = db.Column(db.String(50)) # e.g., FT2733, can be null for PRs
    order_qty = db.Column(db.Integer, nullable=False)
    ets_date = db.Column(db.DateTime) # Estimated Time of Arrival
    status = db.Column(db.String(50)) # 'Ordered', 'Shipped', 'Received'
    confirmation_status = db.Column(db.String(50), default='Pending') # 'Pending', 'Confirmed' (formerly PR status)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to user_location
    user_location = db.relationship('UserLocation', backref='orders', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} Status:{self.status}>'

# 4. Sales & Pricing
class Pricing(db.Model):
    __tablename__ = 'pricing'
    id = db.Column('pricing_id', db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    lsp_price = db.Column(db.Float) # List Selling Price
    wm_price = db.Column(db.Float) # West Malaysia Price
    em_price = db.Column(db.Float) # East Malaysia Price
    effective_date = db.Column(db.DateTime, default=datetime.utcnow)

    campaigns = db.relationship('Campaign', backref='pricing', lazy=True)

    def __repr__(self):
        return f'<Pricing P:{self.product_id}>'

class Campaign(db.Model):
    __tablename__ = 'campaign'
    id = db.Column('campaign_id', db.Integer, primary_key=True)
    pricing_id = db.Column(db.Integer, db.ForeignKey('pricing.pricing_id'), nullable=False)
    campaign_name = db.Column(db.String(200))
    gift_item = db.Column(db.String(200))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Campaign {self.campaign_name}>'

class Sale(db.Model):
    __tablename__ = 'sale'
    id = db.Column('sale_id', db.Integer, primary_key=True)
    pl_id = db.Column(db.Integer, db.ForeignKey('product_loc.pl_id'), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    quantity_sold = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(200))
    sold_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __repr__(self):
        return f'<Sale {self.id} Qty:{self.quantity_sold}>'

class Invoice(db.Model):
    __tablename__ = 'invoice'
    id = db.Column('invoice_id', db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.sale_id'), nullable=False)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)

    sale = db.relationship('Sale', backref=db.backref('invoice', uselist=False))

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

# 5. Forecast (Optional/Legacy but good to keep for "AI" features if needed)
# I will keep a simplified version linked to Product for the dashboard AI features
class Forecast(db.Model):
    __tablename__ = 'forecast'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    projected_demand = db.Column(db.Integer)
    confidence_score = db.Column(db.Float)
    smart_why_rationale = db.Column(db.Text)

    product = db.relationship('Product', backref=db.backref('forecast', uselist=False))

    def __repr__(self):
        return f'<Forecast P:{self.product_id}>'
