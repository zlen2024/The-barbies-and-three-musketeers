from app import app, db
from models import User, Product, Inventory, HistoricalSales, Forecast, PurchaseRequest, Vendor
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

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
        db.session.commit()  # Commit users to get IDs

        print("Seeding Vendors...")
        # Vendors
        vendors = [
            Vendor(vendor_name='GlobalPort Logistics', contact_email='orders@globalport.com'),
            Vendor(vendor_name='Apex Kitchen Supplies', contact_email='sales@apexkitchen.com'),
            Vendor(vendor_name='Nordic Ware', contact_email='b2b@nordicware.com'),
            Vendor(vendor_name='TechSource Inc.', contact_email='orders@techsource.com'),
            Vendor(vendor_name='OfficeDepot B2B', contact_email='support@officedepot.com')
        ]
        db.session.add_all(vendors)
        db.session.commit()

        print("Seeding Products...")
        # Products
        products = [
            Product(sku_id='TACT1-M323/XB-P', product_name='Smart Induction Hood X1', category='Kitchen Appliances / Ducting', unit_price=450.00, lead_time=30, minimum_stock_level=100),
            Product(sku_id='ERGO-PRO-V2', product_name='ErgoChair Pro V2', category='Office Furniture', unit_price=299.00, lead_time=14, minimum_stock_level=50),
            Product(sku_id='AUDIO-NC-100', product_name='Wireless Noise Cancelling Headphones', category='Electronics', unit_price=120.00, lead_time=7, minimum_stock_level=200),
            Product(sku_id='MONITOR-4K-27', product_name='UltraClear 4K Monitor 27"', category='Electronics', unit_price=350.00, lead_time=21, minimum_stock_level=80),
            Product(sku_id='DESK-SITSTAND', product_name='Smart Sit-Stand Desk', category='Office Furniture', unit_price=550.00, lead_time=25, minimum_stock_level=40),
            Product(sku_id='BLEND-PRO-X', product_name='Pro Series Blender', category='Kitchen Appliances', unit_price=180.00, lead_time=10, minimum_stock_level=60),
            Product(sku_id='COFFEE-AUTO', product_name='Automatic Espresso Machine', category='Kitchen Appliances', unit_price=800.00, lead_time=45, minimum_stock_level=20),
            Product(sku_id='LAPTOP-STAND', product_name='Aluminum Laptop Stand', category='Office Accessories', unit_price=45.00, lead_time=5, minimum_stock_level=150),
            Product(sku_id='MOUSE-ERGONOMIC', product_name='Ergonomic Vertical Mouse', category='Electronics', unit_price=35.00, lead_time=7, minimum_stock_level=120),
            Product(sku_id='KEYBOARD-MECH', product_name='Mechanical Keyboard RGB', category='Electronics', unit_price=110.00, lead_time=14, minimum_stock_level=90),
        ]

        # Assign vendors to products
        products[0].vendors.extend([vendors[0], vendors[1]])
        products[1].vendors.append(vendors[4])
        products[2].vendors.append(vendors[3])
        products[3].vendors.append(vendors[3])
        products[4].vendors.append(vendors[4])
        products[5].vendors.append(vendors[1])
        products[6].vendors.extend([vendors[1], vendors[2]])
        products[7].vendors.append(vendors[4])
        products[8].vendors.append(vendors[3])
        products[9].vendors.append(vendors[3])

        db.session.add_all(products)
        db.session.commit()

        print("Seeding Inventory...")
        # Inventory
        inventories = [
            Inventory(sku_id_fk=products[0].id, total_stock_on_hand=412, incoming_stock=500, stock_aging_days=15),
            Inventory(sku_id_fk=products[1].id, total_stock_on_hand=20, incoming_stock=0, stock_aging_days=45),
            Inventory(sku_id_fk=products[2].id, total_stock_on_hand=300, incoming_stock=100, stock_aging_days=5),
            Inventory(sku_id_fk=products[3].id, total_stock_on_hand=90, incoming_stock=50, stock_aging_days=10),
            Inventory(sku_id_fk=products[4].id, total_stock_on_hand=35, incoming_stock=20, stock_aging_days=25),
            Inventory(sku_id_fk=products[5].id, total_stock_on_hand=70, incoming_stock=30, stock_aging_days=12),
            Inventory(sku_id_fk=products[6].id, total_stock_on_hand=15, incoming_stock=10, stock_aging_days=60),
            Inventory(sku_id_fk=products[7].id, total_stock_on_hand=200, incoming_stock=100, stock_aging_days=8),
            Inventory(sku_id_fk=products[8].id, total_stock_on_hand=150, incoming_stock=50, stock_aging_days=20),
            Inventory(sku_id_fk=products[9].id, total_stock_on_hand=100, incoming_stock=40, stock_aging_days=18),
        ]
        db.session.add_all(inventories)

        print("Seeding Sales History...")
        sales_channels = ['Lazada', 'Shopee', 'E-store', 'TikTok', 'Projects', 'Warehouse']
        today = datetime.utcnow()

        # Generate sales for the last 6 months for each product
        for product in products:
            # Base sales volume varies by product
            base_volume = random.randint(20, 100)

            # Create sales for each month
            for i in range(6):
                month_date = today - timedelta(days=30 * i)
                # Vary sales by +/- 20%
                monthly_sales = int(base_volume * (1 + random.uniform(-0.2, 0.2)))

                # Split monthly sales across channels
                remaining_sales = monthly_sales
                for channel in sales_channels[:-1]: # All except last one
                    if remaining_sales <= 0: break
                    channel_sales = random.randint(0, remaining_sales)
                    remaining_sales -= channel_sales
                    if channel_sales > 0:
                        sale = HistoricalSales(
                            sku_id_fk=product.id,
                            quantity_sold=channel_sales,
                            sales_channel=channel,
                            transaction_date=month_date
                        )
                        db.session.add(sale)

                # Add remaining to last channel
                if remaining_sales > 0:
                    sale = HistoricalSales(
                        sku_id_fk=product.id,
                        quantity_sold=remaining_sales,
                        sales_channel=sales_channels[-1],
                        transaction_date=month_date
                    )
                    db.session.add(sale)

        print("Seeding Forecasts...")
        # Forecasts
        forecasts = [
            Forecast(sku_id_fk=products[0].id, projected_demand=120, confidence_score=0.89, smart_why_rationale="Based on the 12% sales acceleration this month and the upcoming 12-day lead time increase from GlobalPort, we are projecting a stockout in 14 days."),
            Forecast(sku_id_fk=products[1].id, projected_demand=60, confidence_score=0.92, smart_why_rationale="Seasonal demand spike expected due to Back-to-School sales. Current stock is critically low."),
            Forecast(sku_id_fk=products[2].id, projected_demand=150, confidence_score=0.85, smart_why_rationale="Stable demand with minor fluctuations. Recommended to maintain current stock levels."),
            Forecast(sku_id_fk=products[3].id, projected_demand=80, confidence_score=0.88, smart_why_rationale="Increased demand from corporate clients expected next month."),
            Forecast(sku_id_fk=products[4].id, projected_demand=40, confidence_score=0.75, smart_why_rationale="New product launch in competitor market may affect sales."),
            Forecast(sku_id_fk=products[5].id, projected_demand=90, confidence_score=0.90, smart_why_rationale="High demand season approaching for kitchen appliances."),
            Forecast(sku_id_fk=products[6].id, projected_demand=25, confidence_score=0.95, smart_why_rationale="Premium product with consistent low volume sales."),
            Forecast(sku_id_fk=products[7].id, projected_demand=180, confidence_score=0.80, smart_why_rationale="High volume, low margin product. Monitor inventory turnover closely."),
            Forecast(sku_id_fk=products[8].id, projected_demand=130, confidence_score=0.82, smart_why_rationale="Steady sales across all online channels."),
            Forecast(sku_id_fk=products[9].id, projected_demand=100, confidence_score=0.87, smart_why_rationale="Gaming season boosting mechanical keyboard sales.")
        ]
        db.session.add_all(forecasts)

        print("Seeding Purchase Requests...")
        # Purchase Requests
        prs = [
            PurchaseRequest(sku_id_fk=products[0].id, requested_quantity=100, status='Pending', created_by=admin_user.id, timestamp=today - timedelta(days=2)),
            PurchaseRequest(sku_id_fk=products[0].id, requested_quantity=200, status='Approved', created_by=admin_user.id, timestamp=today - timedelta(days=10)),
            PurchaseRequest(sku_id_fk=products[1].id, requested_quantity=50, status='Pending', created_by=sales_user.id, timestamp=today - timedelta(days=1)),
            PurchaseRequest(sku_id_fk=products[2].id, requested_quantity=150, status='Rejected', created_by=admin_user.id, timestamp=today - timedelta(days=5)),
            PurchaseRequest(sku_id_fk=products[3].id, requested_quantity=80, status='Approved', created_by=sales_user.id, timestamp=today - timedelta(days=15)),
        ]
        db.session.add_all(prs)

        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
