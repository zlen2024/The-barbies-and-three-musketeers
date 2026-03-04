from app import app, db
from models import User, Product, Location, ProductLoc, Vendor, ProductVendor, ProductOrder, Pricing, Campaign, Sale, Forecast, UserLocation, Invoice
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    with app.app_context():
        # Clean slate
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        print("Seeding Users...")
        # Users
        users = [
            User(username='admin', password_hash=generate_password_hash('password'), role='Admin'),
            User(username='warehouse', password_hash=generate_password_hash('password'), role='Warehouse'),
            User(username='sales', password_hash=generate_password_hash('password'), role='Sales'),
            User(username='manager', password_hash=generate_password_hash('password'), role='Manager')
        ]
        db.session.add_all(users)
        db.session.commit()

        print("Seeding Locations...")
        locations = [
            Location(loc_code='WH-MAIN', description='Main Warehouse', type='Physical Warehouse', address='123 Main Industrial Park', region='West Malaysia'),
            Location(loc_code='WH-REWORK', description='Rework Area', type='Physical Warehouse', address='123 Main Industrial Park, Block B', region='West Malaysia'),
            Location(loc_code='CH-LAZADA', description='Lazada Online Store', type='Online Channel', address='Virtual Hub - Lazada', region='All Malaysia'),
            Location(loc_code='CH-SHOPEE', description='Shopee Online Store', type='Online Channel', address='Virtual Hub - Shopee', region='All Malaysia'),
            Location(loc_code='CH-TIKTOK', description='TikTok Shop', type='Online Channel', address='Virtual Hub - TikTok', region='All Malaysia'),
            Location(loc_code='CH-ESTORE', description='Direct E-Store', type='Online Channel', address='HQ Server Room', region='All Malaysia')
        ]
        db.session.add_all(locations)
        db.session.commit()

        print("Seeding User Locations...")
        user_locations = [
            # Assign warehouse user to WH-MAIN and WH-REWORK
            UserLocation(uid=users[1].id, location_id=locations[0].id),
            UserLocation(uid=users[1].id, location_id=locations[1].id),
            # Assign sales user to CH-LAZADA and CH-SHOPEE
            UserLocation(uid=users[2].id, location_id=locations[2].id),
            UserLocation(uid=users[2].id, location_id=locations[3].id),
        ]
        db.session.add_all(user_locations)
        db.session.commit()

        print("Seeding Vendors...")
        vendors = [
            Vendor(vendor_name='GlobalPort Logistics', contact_person='John Doe', phone_number='+123456789', is_overseas=True),
            Vendor(vendor_name='Apex Kitchen Supplies', contact_person='Jane Smith', phone_number='+987654321', is_overseas=False),
            Vendor(vendor_name='Nordic Ware', contact_person='Bob Johnson', phone_number='+1122334455', is_overseas=True),
            Vendor(vendor_name='TechSource Inc.', contact_person='Alice Brown', phone_number='+5566778899', is_overseas=False),
            Vendor(vendor_name='Rubine Manufacturer', contact_person='Charlie Green', phone_number='+9988776655', is_overseas=False)
        ]
        db.session.add_all(vendors)
        db.session.commit()

        print("Seeding Products...")
        products = [
            Product(model_code='HT-PLATZ-450-H', product_name='Granite Sink Platz 450', category='Granite Sink', brand='Rubine', status='Active'),
            Product(model_code='SIROCCO-XR-BL', product_name='Sirocco XR Hood', category='Hood Cooker', brand='Rubine', status='Active'),
            Product(model_code='RWH-2388-B', product_name='Instant Water Heater', category='Water Heater', brand='Rubine', status='Active'),
            Product(model_code='FX-1200-SS', product_name='Stainless Steel Sink FX', category='Stainless Sink', brand='Haustern', status='Active'),
            Product(model_code='MT-5050-G', product_name='Mixer Tap Gold', category='Taps', brand='Haustern', status='Active'),
            Product(model_code='OV-60-EL', product_name='Electric Oven 60L', category='Oven', brand='Elba', status='Discontinued'),
            Product(model_code='HB-2-GAS', product_name='2-Burner Gas Hob', category='Hob', brand='Rubine', status='Active'),
            Product(model_code='DISH-X1', product_name='Dishwasher X1 Pro', category='Dishwasher', brand='Bosch', status='Active'),
            Product(model_code='ACC-RACK-S', product_name='Spice Rack Small', category='Accessories', brand='OEM', status='Active'),
            Product(model_code='ACC-DRAIN', product_name='Drainer Basket', category='Accessories', brand='OEM', status='Active')
        ]
        db.session.add_all(products)
        db.session.commit()

        print("Seeding Product Vendors...")
        # Link products to vendors
        product_vendors = []
        for prod in products:
            # Assign random vendors (1 or 2 per product)
            assigned_vendors = random.sample(vendors, k=random.randint(1, 2))
            for v in assigned_vendors:
                cost = round(random.uniform(50, 500), 2)
                lead_time = random.choice([7, 14, 30, 45, 60])
                product_vendors.append(ProductVendor(product_id=prod.id, vendor_id=v.id, cost_price=cost, lead_time_days=lead_time))

        db.session.add_all(product_vendors)
        db.session.commit()

        print("Seeding Pricing & Campaigns...")
        pricings = []
        campaigns = []
        for prod in products:
            base_price = round(random.uniform(100, 1000), 2)
            pricing = Pricing(
                product_id=prod.id,
                lsp_price=base_price,
                wm_price=round(base_price * 1.1, 2),
                em_price=round(base_price * 1.2, 2),
                effective_date=datetime.utcnow() - timedelta(days=365)
            )
            pricings.append(pricing)

            # Add a campaign for some products
            if random.choice([True, False]):
                campaigns.append(Campaign(
                    pricing_id=pricing.id, # We need ID, so we might need to flush or add separately
                    campaign_name=f"Promo for {prod.model_code}",
                    gift_item="Free Cleaning Kit",
                    start_date=datetime.utcnow() - timedelta(days=30),
                    end_date=datetime.utcnow() + timedelta(days=30)
                ))

        db.session.add_all(pricings)
        db.session.commit()

        # Link campaigns to pricing IDs
        for camp, price in zip(campaigns, [p for p in pricings if p in [c.pricing for c in campaigns] or True]): # Logic tricky here due to zip list length match
             # Simplification: Just loop pricings and add campaigns
             pass

        # Better approach for campaigns:
        for p in pricings:
            if random.random() > 0.7:
                 db.session.add(Campaign(
                    pricing_id=p.id,
                    campaign_name=f"Promo Campaign 2024",
                    gift_item="Mystery Gift",
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=60)
                ))
        db.session.commit()

        print("Seeding Product Locations (Inventory)...")
        product_locs = []
        for prod in products:
            # Stock in Main Warehouse
            qty = random.randint(0, 500)
            pl_main = ProductLoc(product_id=prod.id, location_id=locations[0].id, quantity_on_hand=qty, updated_by=users[1].id)
            product_locs.append(pl_main)

            # Stock in Rework
            if random.random() > 0.8:
                product_locs.append(ProductLoc(product_id=prod.id, location_id=locations[1].id, quantity_on_hand=random.randint(0, 20), updated_by=users[1].id))

            # Stock in Channels (usually logical stock, but schema treats as Location)
            # Maybe 0 quantity here if it's just a channel, or allocated stock.
            # Let's put some "stock" in channels to simulate channel-specific allocation
            for loc in locations[2:]:
                if random.random() > 0.5:
                     product_locs.append(ProductLoc(product_id=prod.id, location_id=loc.id, quantity_on_hand=random.randint(0, 50), updated_by=users[2].id))

        db.session.add_all(product_locs)
        db.session.commit()

        print("Seeding Sales...")
        # Generate sales linked to ProductLocs
        sales = []
        today = datetime.utcnow()
        for pl in product_locs:
            # Generate sales for the past 6 months
            if pl.location.type == 'Online Channel':
                # Online channels sell more
                for i in range(20):
                     qty = random.randint(1, 5)
                     date = today - timedelta(days=random.randint(1, 180))
                     sale = Sale(pl_id=pl.id, sale_date=date, quantity_sold=qty, sold_by=users[2].id, customer_name=f"Customer {random.randint(1000,9999)}")
                     sales.append(sale)
                     db.session.add(sale)
            else:
                # Warehouse sales (e.g. direct orders)
                 for i in range(5):
                     qty = random.randint(10, 50)
                     date = today - timedelta(days=random.randint(1, 180))
                     sale = Sale(pl_id=pl.id, sale_date=date, quantity_sold=qty, sold_by=users[1].id, customer_name=f"Distributor {random.randint(100,999)}")
                     sales.append(sale)
                     db.session.add(sale)

        db.session.commit() # commit sales to get their IDs

        print("Seeding Invoices...")
        invoices = []
        for idx, sale in enumerate(sales):
            # Try to get pricing for total amount estimation
            price = 100.0 # Default price
            if sale.product_loc.product.pricing:
                price = sale.product_loc.product.pricing[0].lsp_price or 100.0

            invoice = Invoice(
                sale_id=sale.id,
                invoice_number=f"INV-{sale.sale_date.strftime('%Y%m%d')}-{1000 + idx}",
                generated_date=sale.sale_date + timedelta(hours=1),
                total_amount=price * sale.quantity_sold
            )
            invoices.append(invoice)

        db.session.add_all(invoices)
        db.session.commit()

        print("Seeding Orders (POs & PRs)...")
        # Find ProductVendors to order from
        pvs = ProductVendor.query.all()
        orders = []
        for i in range(10):
            pv = random.choice(pvs)
            # Confirmed PO
            orders.append(ProductOrder(
                pv_id=pv.id,
                ul_id=user_locations[0].ul_id, # Link to warehouse user's location
                po_reference=f"PO-2024-{random.randint(1000,9999)}",
                order_qty=random.randint(50, 200),
                ets_date=today + timedelta(days=pv.lead_time_days),
                status='Ordered',
                confirmation_status='Confirmed',
                created_by=users[1].id # Warehouse user
            ))

            # Unconfirmed PR
            orders.append(ProductOrder(
                pv_id=pv.id,
                ul_id=user_locations[0].ul_id, # Link to warehouse user's location
                po_reference=None,
                order_qty=random.randint(20, 100),
                ets_date=None,
                status='Pending', # Internal status
                confirmation_status='Pending', # PR status
                created_by=users[1].id # Warehouse user
            ))

        db.session.add_all(orders)
        db.session.commit()

        print("Seeding Forecasts (Legacy/AI)...")
        forecasts = []
        for prod in products:
             forecasts.append(Forecast(
                 product_id=prod.id,
                 projected_demand=random.randint(50, 300),
                 confidence_score=random.uniform(0.7, 0.99),
                 smart_why_rationale=f"Simulated AI rationale for {prod.model_code} based on recent sales velocity."
             ))
        db.session.add_all(forecasts)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
