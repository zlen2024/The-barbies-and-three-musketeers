import re

with open('app.py', 'r') as f:
    content = f.read()

# Make sure we don't accidentally do multiple patches
def add_try_except(func_name, block_code, error_message, extra_indent=""):
    # This is slightly tricky, we'll find the whole function and replace its body
    pass

# Alternatively, we can use regex to wrap `db.session.commit()` calls
# Or just replace the functions manually in Python to be safe.

# api_generate_pr
api_generate_pr_old = """        db.session.add(pr)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Purchase Request created for {product.model_code}'})"""
api_generate_pr_new = """        try:
            db.session.add(pr)
            db.session.commit()
            logger.info(f"Purchase Request created successfully for {product.model_code} by user {current_user.username}")
            return jsonify({'success': True, 'message': f'Purchase Request created for {product.model_code}'})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create Purchase Request for {product.model_code}: {str(e)}\\n{traceback.format_exc()}")
            return jsonify({'success': False, 'message': 'Database error occurred while creating Purchase Request'}), 500"""
content = content.replace(api_generate_pr_old, api_generate_pr_new)

# api_add_product
api_add_product_old = """    db.session.add(new_product)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Product added successfully', 'id': new_product.id})"""
api_add_product_new = """    try:
        db.session.add(new_product)
        db.session.commit()
        logger.info(f"Product added successfully: {model_code} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Product added successfully', 'id': new_product.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add Product {model_code}: {str(e)}\\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Database error occurred while adding Product'}), 500"""
content = content.replace(api_add_product_old, api_add_product_new)

# api_add_vendor
api_add_vendor_old = """    db.session.add(new_vendor)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Vendor added successfully', 'id': new_vendor.id})"""
api_add_vendor_new = """    try:
        db.session.add(new_vendor)
        db.session.commit()
        logger.info(f"Vendor added successfully: {vendor_name} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Vendor added successfully', 'id': new_vendor.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add Vendor {vendor_name}: {str(e)}\\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Database error occurred while adding Vendor'}), 500"""
content = content.replace(api_add_vendor_old, api_add_vendor_new)

# api_confirm_order
api_confirm_order_old = """    order.status = 'Ordered' # Set initial status to Ordered once confirmed
    # Set ETA mock
    order.ets_date = datetime.utcnow() + timedelta(days=order.product_vendor.lead_time_days or 14)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Order confirmed successfully'})"""
api_confirm_order_new = """    order.status = 'Ordered' # Set initial status to Ordered once confirmed
    # Set ETA mock
    order.ets_date = datetime.utcnow() + timedelta(days=order.product_vendor.lead_time_days or 14)

    try:
        db.session.commit()
        logger.info(f"Order confirmed successfully: ID {order_id} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Order confirmed successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to confirm Order ID {order_id}: {str(e)}\\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Database error occurred while confirming Order'}), 500"""
content = content.replace(api_confirm_order_old, api_confirm_order_new)

# api_sales POST
api_sales_old = """    sale = Sale(
        pl_id=pl_id,
        quantity_sold=int(quantity_sold),
        customer_name=customer_name,
        sold_by=current_user.id
    )
    db.session.add(sale)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Sale added successfully', 'sale_id': sale.id})"""
api_sales_new = """    sale = Sale(
        pl_id=pl_id,
        quantity_sold=int(quantity_sold),
        customer_name=customer_name,
        sold_by=current_user.id
    )
    try:
        db.session.add(sale)
        db.session.commit()
        logger.info(f"Sale added successfully: PL ID {pl_id}, Qty {quantity_sold} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Sale added successfully', 'sale_id': sale.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add Sale for PL ID {pl_id}: {str(e)}\\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Database error occurred while adding Sale'}), 500"""
content = content.replace(api_sales_old, api_sales_new)

# api_invoices POST
api_invoices_old = """    invoice = Invoice(
        sale_id=sale_id,
        invoice_number=invoice_number,
        total_amount=float(total_amount)
    )
    db.session.add(invoice)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Invoice generated successfully', 'invoice_id': invoice.id})"""
api_invoices_new = """    invoice = Invoice(
        sale_id=sale_id,
        invoice_number=invoice_number,
        total_amount=float(total_amount)
    )
    try:
        db.session.add(invoice)
        db.session.commit()
        logger.info(f"Invoice generated successfully: Sale ID {sale_id}, Invoice Number {invoice_number} by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Invoice generated successfully', 'invoice_id': invoice.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to generate Invoice for Sale ID {sale_id}: {str(e)}\\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Database error occurred while generating Invoice'}), 500"""
content = content.replace(api_invoices_old, api_invoices_new)

# api_assign_location POST
api_assign_location_old = """    user_location = UserLocation(
        uid=uid,
        location_id=location_id
    )
    db.session.add(user_location)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Location assigned to user successfully', 'ul_id': user_location.ul_id})"""
api_assign_location_new = """    user_location = UserLocation(
        uid=uid,
        location_id=location_id
    )
    try:
        db.session.add(user_location)
        db.session.commit()
        logger.info(f"Location {location_id} assigned to user {uid} successfully by user {current_user.username}")
        return jsonify({'success': True, 'message': 'Location assigned to user successfully', 'ul_id': user_location.ul_id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to assign Location {location_id} to User {uid}: {str(e)}\\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Database error occurred while assigning Location'}), 500"""
content = content.replace(api_assign_location_old, api_assign_location_new)

with open('app.py', 'w') as f:
    f.write(content)
