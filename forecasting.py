import os
import pandas as pd
from datetime import datetime, timedelta
import threading
from nixtla import NixtlaClient
from models import db, Sale, SaleItem, ProductLoc, Product, TimeSeriesForecast

def _fetch_actual_sales_data(app, product_id=None):
    """
    Fetch the last 140 days of actual sales, grouped by week (starting Monday).
    Returns a DataFrame suitable for TimeGEN-1.
    """
    with app.app_context():
        end_date = datetime.now()
        start_date = end_date - timedelta(days=140)

        query = db.session.query(
            db.func.date(Sale.sale_date).label('date'),
            db.func.sum(SaleItem.quantity).label('total_quantity')
        ).join(SaleItem, SaleItem.sale_id == Sale.id)

        if product_id is not None:
            query = query.join(ProductLoc, SaleItem.pl_id == ProductLoc.id).filter(
                ProductLoc.product_id == product_id
            )

        query = query.filter(Sale.sale_date >= start_date, Sale.sale_date <= end_date)
        sales_data = query.group_by(db.func.date(Sale.sale_date)).all()

        if not sales_data:
            return None

        # Create continuous daily series first
        sales_dict = {str(sale.date): sale.total_quantity for sale in sales_data}
        daily_sales = []
        for i in range(140):
            target_date = start_date + timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            daily_sales.append({
                'timestamp': target_date,
                'value': sales_dict.get(date_str, 0)
            })

        df = pd.DataFrame(daily_sales)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Resample by week ending on Monday (W-MON)
        df.set_index('timestamp', inplace=True)
        weekly_df = df.resample('W-MON').sum().reset_index()

        # Remove the very last incomplete week to prevent artificial drops
        if not weekly_df.empty:
            weekly_df = weekly_df.iloc[:-1]

        return weekly_df

def run_forecast_task(app):
    """
    Background task to run forecast for all products and the total dashboard.
    """
    print("Starting background forecast task...")

    api_key = os.environ.get('AZURE_TIMEGEN_API_KEY', 'xLGggD2gRexIbzcLiMGvC2Qfly1xaH7V')
    base_url = os.environ.get('AZURE_TIMEGEN_ENDPOINT', 'https://TimeGEN-1-ChinHin.eastus2.models.ai.azure.com')

    try:
        nixtla_client = NixtlaClient(base_url=base_url, api_key=api_key)
    except Exception as e:
        print(f"Error initializing Nixtla client: {e}")
        return

    with app.app_context():
        products = Product.query.all()
        product_ids = [p.id for p in products] + [None] # None is for the total dashboard

        for pid in product_ids:
            try:
                df = _fetch_actual_sales_data(app, pid)
                if df is None or len(df) < 5:
                    print(f"Not enough data to forecast for product_id={pid}")
                    continue

                # We forecast 9 weeks
                timegen_fcst_df = nixtla_client.forecast(
                    df=df,
                    h=9,
                    freq='W-MON',
                    time_col='timestamp',
                    target_col='value'
                )

                # Delete old forecasts for this product/global
                if pid is None:
                    db.session.query(TimeSeriesForecast).filter(TimeSeriesForecast.product_id == None).delete()
                else:
                    db.session.query(TimeSeriesForecast).filter(TimeSeriesForecast.product_id == pid).delete()

                # Insert new forecasts
                for index, row in timegen_fcst_df.iterrows():
                    # Check which column contains the prediction. Usually it's 'TimeGPT' or 'TimeGEN'
                    pred_col = 'TimeGPT' if 'TimeGPT' in row else ('TimeGEN' if 'TimeGEN' in row else row.index[-1])
                    val = max(0, float(row[pred_col])) # Ensure no negative forecasts

                    forecast_entry = TimeSeriesForecast(
                        product_id=pid,
                        forecast_date=row['timestamp'],
                        predicted_value=val
                    )
                    db.session.add(forecast_entry)

                db.session.commit()
                print(f"Successfully generated forecast for product_id={pid}")

            except Exception as e:
                print(f"Error forecasting for product_id={pid}: {e}")
                db.session.rollback()

    print("Finished background forecast task.")

def schedule_forecasting(app):
    """
    Start the APScheduler for daily updates and run the first iteration immediately in a thread.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    import atexit
    import threading

    def delayed_run():
        import time
        # Delay initial run slightly to allow seed_data.py to create the database tables
        print("Waiting 10 seconds before starting background forecast task to allow database seeding...")
        time.sleep(10)
        run_forecast_task(app)

    # Run once immediately (after delay)
    thread = threading.Thread(target=delayed_run)
    thread.daemon = True
    thread.start()

    # Schedule daily at 12:00 AM
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_forecast_task, trigger="cron", hour=0, minute=0, args=[app])
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown(wait=False))