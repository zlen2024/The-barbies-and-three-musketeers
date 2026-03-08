from app import app, db
from models import User, Product, Location, ProductLoc, Vendor, ProductVendor, ProductOrder, Pricing, Campaign, Sale, SaleItem, Forecast, UserLocation, Invoice, InternalMail
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
            User(username='testadmin', email='testadmin@chinhinforcast.com', password_hash=generate_password_hash('password', method='pbkdf2:sha256'), role='Admin'),
            User(username='testwarehouse', email='testwarehouse@chinhinforcast.com', password_hash=generate_password_hash('password', method='pbkdf2:sha256'), role='Warehouse'),
            User(username='testsales', email='testsales@chinhinforcast.com', password_hash=generate_password_hash('password', method='pbkdf2:sha256'), role='Sales'),
            User(username='testmanager', email='testmanager@chinhinforcast.com', password_hash=generate_password_hash('password', method='pbkdf2:sha256'), role='Manager'),
            User(username='testwarehouse2', email='testwarehouse2@chinhinforcast.com', password_hash=generate_password_hash('password', method='pbkdf2:sha256'), role='Warehouse'),
            User(username='testsales2', email='testsales2@chinhinforcast.com', password_hash=generate_password_hash('password', method='pbkdf2:sha256'), role='Sales')
        ]
        db.session.add_all(users)
        db.session.commit()

        print("Seeding Locations...")
        locations = [
            Location(loc_code='test-WH-MAIN', description='test Main Warehouse', type='Physical Warehouse', address='test 123 Main Industrial Park', region='West Malaysia'),
            Location(loc_code='test-WH-REWORK', description='test Rework Area', type='Physical Warehouse', address='test 123 Main Industrial Park, Block B', region='West Malaysia'),
            Location(loc_code='test-CH-LAZADA', description='test Lazada Online Store', type='Online Channel', address='test Virtual Hub - Lazada', region='All Malaysia'),
            Location(loc_code='test-CH-SHOPEE', description='test Shopee Online Store', type='Online Channel', address='test Virtual Hub - Shopee', region='All Malaysia'),
            Location(loc_code='test-CH-TIKTOK', description='test TikTok Shop', type='Online Channel', address='test Virtual Hub - TikTok', region='All Malaysia'),
            Location(loc_code='test-CH-ESTORE', description='test Direct E-Store', type='Online Channel', address='test HQ Server Room', region='All Malaysia')
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
            # Assign testwarehouse2 to WH-MAIN and WH-REWORK
            UserLocation(uid=users[4].id, location_id=locations[0].id),
            UserLocation(uid=users[4].id, location_id=locations[1].id),
            # Assign testsales2 to CH-TIKTOK and CH-ESTORE
            UserLocation(uid=users[5].id, location_id=locations[4].id),
            UserLocation(uid=users[5].id, location_id=locations[5].id),
        ]
        db.session.add_all(user_locations)
        db.session.commit()

        print("Seeding Vendors...")
        vendors = [
            Vendor(vendor_name='test GlobalPort Logistics', contact_person='test John Doe', phone_number='+123456789', is_overseas=True),
            Vendor(vendor_name='test Apex Kitchen Supplies', contact_person='test Jane Smith', phone_number='+987654321', is_overseas=False),
            Vendor(vendor_name='test Nordic Ware', contact_person='test Bob Johnson', phone_number='+1122334455', is_overseas=True),
            Vendor(vendor_name='test TechSource Inc.', contact_person='test Alice Brown', phone_number='+5566778899', is_overseas=False),
            Vendor(vendor_name='test Rubine Manufacturer', contact_person='test Charlie Green', phone_number='+9988776655', is_overseas=False)
        ]
        db.session.add_all(vendors)
        db.session.commit()

        print("Seeding Products...")
        products = [
            Product(model_code='test-HT-PLATZ-450-H', product_name='test Granite Sink Platz 450', category='Granite Sink', brand='test Rubine', status='Active'),
            Product(model_code='test-SIROCCO-XR-BL', product_name='test Sirocco XR Hood', category='Hood Cooker', brand='test Rubine', status='Active'),
            Product(model_code='test-RWH-2388-B', product_name='test Instant Water Heater', category='Water Heater', brand='test Rubine', status='Active'),
            Product(model_code='test-FX-1200-SS', product_name='test Stainless Steel Sink FX', category='Stainless Sink', brand='test Haustern', status='Active'),
            Product(model_code='test-MT-5050-G', product_name='test Mixer Tap Gold', category='Taps', brand='test Haustern', status='Active'),
            Product(model_code='test-OV-60-EL', product_name='test Electric Oven 60L', category='Oven', brand='test Elba', status='Discontinued'),
            Product(model_code='test-HB-2-GAS', product_name='test 2-Burner Gas Hob', category='Hob', brand='test Rubine', status='Active'),
            Product(model_code='test-DISH-X1', product_name='test Dishwasher X1 Pro', category='Dishwasher', brand='test Bosch', status='Active'),
            Product(model_code='test-ACC-RACK-S', product_name='test Spice Rack Small', category='Accessories', brand='test OEM', status='Active'),
            Product(model_code='test-ACC-DRAIN', product_name='test Drainer Basket', category='Accessories', brand='test OEM', status='Active')
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
                    campaign_name=f"test Promo for {prod.model_code}",
                    gift_item="test Free Cleaning Kit",
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
                    campaign_name=f"test Promo Campaign 2024",
                    gift_item="test Mystery Gift",
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
        sale_items = []
        today = datetime.utcnow()
        for pl in product_locs:
            # Generate sales for the past 6 months
            if pl.location.type == 'Online Channel':
                # Online channels sell more
                for i in range(20):
                     qty = random.randint(1, 5)
                     date = today - timedelta(days=random.randint(1, 180))

                     price = 100.0
                     if pl.product.pricing:
                         price = pl.product.pricing[0].lsp_price or 100.0

                     sale = Sale(location_id=pl.location_id, sale_date=date, sold_by=users[2].id, customer_name=f"test Customer {random.randint(1000,9999)}", status="Paid", client_email=f"testcustomer{random.randint(1000,9999)}@example.com", total_amount=price * qty)
                     db.session.add(sale)
                     db.session.flush() # get sale.id
                     sales.append(sale)

                     sale_item = SaleItem(sale_id=sale.id, pl_id=pl.id, quantity=qty, unit_price=price, subtotal=price * qty)
                     sale_items.append(sale_item)
                     db.session.add(sale_item)
            else:
                # Warehouse sales (e.g. direct orders)
                 for i in range(5):
                     qty = random.randint(10, 50)
                     date = today - timedelta(days=random.randint(1, 180))

                     price = 100.0
                     if pl.product.pricing:
                         price = pl.product.pricing[0].lsp_price or 100.0

                     sale = Sale(location_id=pl.location_id, sale_date=date, sold_by=users[1].id, customer_name=f"test Distributor {random.randint(100,999)}", status="Paid", client_email=f"testdistributor{random.randint(100,999)}@example.com", total_amount=price * qty)
                     db.session.add(sale)
                     db.session.flush()
                     sales.append(sale)

                     sale_item = SaleItem(sale_id=sale.id, pl_id=pl.id, quantity=qty, unit_price=price, subtotal=price * qty)
                     sale_items.append(sale_item)
                     db.session.add(sale_item)

        db.session.commit()

        print("Seeding Invoices...")
        invoices = []
        for idx, sale in enumerate(sales):
            invoice = Invoice(
                sale_id=sale.id,
                invoice_number=f"test-INV-{sale.sale_date.strftime('%Y%m%d')}-{1000 + idx}",
                generated_date=sale.sale_date + timedelta(hours=1),
                total_amount=sale.total_amount
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
                po_reference=f"test-PO-2024-{random.randint(1000,9999)}",
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
                 smart_why_rationale=f"test Simulated AI rationale for {prod.model_code} based on recent sales velocity."
             ))
        db.session.add_all(forecasts)
        db.session.commit()

        print("Seeding Internal Mail...")
        mails = [
            InternalMail(sender_id=users[3].id, receiver_id=users[1].id, subject='test Warehouse Check', body='test Please ensure the main warehouse has enough HT-PLATZ-450-H.'),
            InternalMail(sender_id=users[3].id, receiver_id=users[2].id, subject='test Sales Target', body='test Great job on the sales this week, let us keep the momentum going.'),
            InternalMail(sender_id=users[1].id, receiver_id=users[3].id, subject='test Re: Warehouse Check', body='test Stock levels checked. We are running low on CH-SINK-SS-1, need to reorder.'),
        ]
        db.session.add_all(mails)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
