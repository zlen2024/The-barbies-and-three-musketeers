import time
import threading
from datetime import datetime, timedelta
import logging
import pandas as pd
from models import db, Product, SaleItem, Sale, ProductLoc
from azure_forecast import trigger_forecast_generation
from sqlalchemy import func
import os

logger = logging.getLogger(__name__)

# To prevent multiple Gunicorn workers from all running the scheduler,
# we can use a simple file lock or just check an environment variable.
# For simplicity in this environment, we'll run it only if we're the main process or worker 1.
# But since the prompt mentions gunicorn is run with --workers=1 --threads=4,
# multiple workers aren't actually an issue. The problem is if the app is imported multiple times.
# We will ensure the scheduler thread is only started once.

_scheduler_started = False

def get_historical_sales_data(product_id=None, days=140):
    """
    Fetch the last 140 days of sales data, aggregated by week (ending on Monday).
    If product_id is None, it aggregates total system-wide sales.
    Returns a list of dicts: [{'timestamp': 'YYYY-MM-DD', 'value': 123.4}]
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    query = db.session.query(
        func.date(Sale.sale_date).label('sale_date'),
        func.sum(SaleItem.quantity).label('total_value')
    ).join(SaleItem, Sale.id == SaleItem.sale_id)

    if product_id:
        query = query.join(ProductLoc, SaleItem.pl_id == ProductLoc.id).filter(ProductLoc.product_id == product_id)

    query = query.filter(Sale.sale_date >= start_date)
    query = query.group_by(func.date(Sale.sale_date))

    results = query.all()

    if not results:
        return []

    # Convert to pandas dataframe to do weekly resampling
    df = pd.DataFrame([{
        'date': r.sale_date,
        'value': float(r.total_value or 0)
    } for r in results])

    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    # Reindex to ensure we cover the entire 140-day period up to today
    full_date_range = pd.date_range(start=start_date.date(), end=end_date.date(), freq='D')
    df = df.reindex(full_date_range, fill_value=0)
    df.index.name = 'date'

    # Resample to 7-day intervals counting backwards from today
    # Instead of W-MON, we can group by a generic 7-day frequency starting from the latest date
    # Pandas '7D' frequency aligns to the start date of the time series.
    # To align so the last chunk ends today, we can reverse the dataframe or manually group.

    df.reset_index(inplace=True)
    df = df.sort_values('date', ascending=False)

    # Group by chunks of 7 days
    chunks = [df.iloc[i:i+7] for i in range(0, len(df), 7)]

    weekly_data = []
    for chunk in chunks:
        if len(chunk) > 0:
            # The label for the chunk is the latest date in that 7-day period
            chunk_latest_date = chunk['date'].max()
            chunk_total_value = chunk['value'].sum()
            weekly_data.append({
                'timestamp': chunk_latest_date.strftime('%Y-%m-%d'),
                'value': chunk_total_value
            })

    # Reverse back to chronological order
    weekly_data.reverse()

    return weekly_data

def run_forecast_job():
    from app import app
    logger.info("Running scheduled forecast job for all products and system-wide.")
    with app.app_context():
        try:
            # 1. System-wide forecast (dashboard)
            system_data = get_historical_sales_data(product_id=None)
            if system_data:
                logger.info("Triggering system-wide forecast")
                trigger_forecast_generation(app, None, system_data)
            else:
                logger.warning("No system-wide sales data found to generate forecast.")

            # 2. Product-specific forecasts
            products = Product.query.all()
            for product in products:
                product_data = get_historical_sales_data(product_id=product.id)
                if product_data:
                    logger.info(f"Triggering forecast for product {product.sku}")
                    trigger_forecast_generation(app, product.id, product_data)
                    # Small sleep to avoid hammering the DB or thread pool simultaneously
                    time.sleep(0.5)
                else:
                    logger.warning(f"No sales data found for product {product.sku} to generate forecast.")
        except Exception as e:
            logger.error(f"Error in scheduled forecast job: {e}")

def forecast_scheduler():
    logger.info("Forecast scheduler thread started.")

    # Run once on startup (wait a few seconds for app to fully boot if needed)
    time.sleep(10)
    run_forecast_job()

    while True:
        now = datetime.now()

        # Check if it's 12:00 AM (00:00)
        # We can run it if hour is 0 and minute is 0
        if now.hour == 0 and now.minute == 0:
            run_forecast_job()
            # Sleep for 61 seconds to avoid triggering multiple times in the same minute
            time.sleep(61)
        else:
            # Sleep for a minute before checking again
            time.sleep(60)

def init_scheduler():
    global _scheduler_started
    # In Flask dev server, Werkzeug restarts the process.
    # To avoid running twice, we can check Werkzeug's internal flag or just use our own.
    # Since Gunicorn only has 1 worker, this boolean is sufficient for the single process.
    if _scheduler_started:
        return

    _scheduler_started = True
    thread = threading.Thread(target=forecast_scheduler)
    thread.daemon = True
    thread.start()
