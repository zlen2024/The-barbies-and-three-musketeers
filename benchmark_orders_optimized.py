import time
from app import app, db
from models import ProductOrder, ProductVendor, Product, Vendor
from sqlalchemy import event
from sqlalchemy.orm import joinedload

def benchmark_orders_endpoint():
    with app.app_context():
        # Count queries
        query_count = 0
        @event.listens_for(db.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        start_time = time.time()

        # Simulate api_get_orders logic with eager loading
        orders = ProductOrder.query.options(
            joinedload(ProductOrder.product_vendor).joinedload(ProductVendor.product),
            joinedload(ProductOrder.product_vendor).joinedload(ProductVendor.vendor)
        ).order_by(ProductOrder.created_at.desc()).all()

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

        end_time = time.time()

        print(f"Number of orders: {len(orders)}")
        print(f"Number of queries: {query_count}")
        print(f"Time taken: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark_orders_endpoint()
