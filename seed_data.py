from app import app, db
from models import User, Product, Inventory, HistoricalSales, Forecast, PurchaseRequest, Vendor
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def seed_database():
    with app.app_context():
        # Clean slate
        db.drop_all()
        db.create_all()

        print("Seeding Users...")
        # Users
        admin_user = User(
            username='admin@inventory.ai',
            password_hash=generate_password_hash('admin123'),
            role='Procurement'
        )
        sales_user = User(
            username='sales@inventory.ai',
            password_hash=generate_password_hash('sales123'),
            role='Sales'
        )
        db.session.add(admin_user)
        db.session.add(sales_user)

        print("Seeding Vendors...")
        # Vendors
        v1 = Vendor(vendor_name='GlobalPort Logistics', contact_email='orders@globalport.com')
        v2 = Vendor(vendor_name='Apex Kitchen Supplies', contact_email='sales@apexkitchen.com')
        v3 = Vendor(vendor_name='Nordic Ware', contact_email='b2b@nordicware.com')
        db.session.add_all([v1, v2, v3])

        print("Seeding Products...")
        # Products
        p1 = Product(
            sku_id='SKU-12345',
            product_name='Smart Induction Hood X1',
            category='Kitchen Appliances',
            unit_price=450.00,
            lead_time=30,
            minimum_stock_level=100
        )
        p1.vendors.append(v1)
        p1.vendors.append(v2)

        p2 = Product(
            sku_id='SKU-67890',
            product_name='ErgoChair Pro V2',
            category='Office Furniture',
            unit_price=299.00,
            lead_time=14,
            minimum_stock_level=50
        )
        p2.vendors.append(v3)

        p3 = Product(
            sku_id='SKU-11223',
            product_name='Wireless Noise Cancelling Headphones',
            category='Electronics',
            unit_price=120.00,
            lead_time=7,
            minimum_stock_level=200
        )

        db.session.add_all([p1, p2, p3])
        db.session.commit() # Commit to get IDs

        print("Seeding Inventory...")
        # Inventory
        i1 = Inventory(
            sku_id_fk=p1.id,
            total_stock_on_hand=80, # Below min stock (100) -> Low Stock
            incoming_stock=50,
            stock_aging_days=15
        )
        i2 = Inventory(
            sku_id_fk=p2.id,
            total_stock_on_hand=20, # Below min stock (50) -> Critical
            incoming_stock=0,
            stock_aging_days=45
        )
        i3 = Inventory(
            sku_id_fk=p3.id,
            total_stock_on_hand=300, # Above min stock (200) -> In Stock
            incoming_stock=100,
            stock_aging_days=5
        )
        db.session.add_all([i1, i2, i3])

        print("Seeding Sales History...")
        # Historical Sales (Just a few records)
        h1 = HistoricalSales(sku_id_fk=p1.id, quantity_sold=10, sales_channel='Lazada', transaction_date=datetime.utcnow() - timedelta(days=2))
        h2 = HistoricalSales(sku_id_fk=p1.id, quantity_sold=5, sales_channel='Shopee', transaction_date=datetime.utcnow() - timedelta(days=5))
        h3 = HistoricalSales(sku_id_fk=p2.id, quantity_sold=2, sales_channel='E-store', transaction_date=datetime.utcnow() - timedelta(days=1))
        db.session.add_all([h1, h2, h3])

        print("Seeding Forecasts...")
        # Forecasts
        f1 = Forecast(
            sku_id_fk=p1.id,
            projected_demand=120,
            confidence_score=0.89,
            smart_why_rationale="Based on the -12% sales acceleration this month and the upcoming 12-day lead time increase from GlobalPort, we are projecting a stockout in 14 days."
        )
        f2 = Forecast(
            sku_id_fk=p2.id,
            projected_demand=60,
            confidence_score=0.92,
            smart_why_rationale="Seasonal demand spike expected due to Back-to-School sales. Current stock is critically low."
        )
        # p3 has no forecast yet
        db.session.add_all([f1, f2])

        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
