import os
import json
import logging
import threading
from datetime import datetime, timedelta
import pandas as pd

from models import db, Forecast

logger = logging.getLogger(__name__)

def generate_forecast_background(app, product_id, sales_data, projection_size=9, sample_size=None):
    """
    Run forecast generation in background using the Nixtla SDK.
    `sales_data` should be a list of dicts: [{'timestamp': 'YYYY-MM-01', 'value': 123.4}, ...]
    `product_id` is the ID of the product, or None for system-wide.
    `projection_size` is the number of periods to forecast (default 9 weeks).
    `sample_size` is the maximum number of historical periods to use (default None = all).
    """
    with app.app_context():
        try:
            logger.info(f"Starting background forecast for product_id={product_id}")
            api_key = os.environ.get('AZURE_TIMEGEN_API_KEY')
            if not api_key:
                logger.error("AZURE_TIMEGEN_API_KEY not found in environment.")
                return

            from nixtla import NixtlaClient

            # Initialize client with Azure endpoint
            client = NixtlaClient(
                base_url="https://TimeGEN-1-ChinHin.eastus2.models.ai.azure.com",
                api_key=api_key
            )

            if not sales_data:
                logger.warning(f"No sales data provided for product_id={product_id}")
                return

            # Prepare dataframe
            df = pd.DataFrame(sales_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Sort by timestamp
            df = df.sort_values(by='timestamp')

            # Apply sample size limit if provided
            if sample_size and int(sample_size) > 0:
                df = df.tail(int(sample_size))

            # Generate forecast
            h_val = int(projection_size) if projection_size else 9
            timegen_fcst_df = client.forecast(
                df=df,
                h=h_val,
                freq='7D',
                time_col='timestamp',
                target_col='value'
            )

            # Process the result
            forecast_results = []

            # Find the prediction column (anything other than timestamp)
            pred_col = None
            for col in timegen_fcst_df.columns:
                if col != 'timestamp':
                    pred_col = col
                    break

            if not pred_col:
                logger.error("No prediction column returned from TimeGEN API.")
                return

            for index, row in timegen_fcst_df.iterrows():
                pred_value = row.get(pred_col, 0)

                if pd.isna(pred_value):
                    pred_value = 0

                # We format it to YYYY-MM-DD for weekly data
                week_str = row['timestamp'].strftime("%Y-%m-%d")
                forecast_results.append({
                    "date": week_str,
                    "value": max(0, float(pred_value)) # Prevent negative forecasts
                })

            # Save to database
            forecast = Forecast.query.filter_by(product_id=product_id).first()
            if not forecast:
                forecast = Forecast(product_id=product_id)
                db.session.add(forecast)

            forecast.forecast_data = json.dumps(forecast_results)
            forecast.last_updated = datetime.now()

            # Simple projected demand is sum of forecast
            forecast.projected_demand = int(sum([f['value'] for f in forecast_results]))

            db.session.commit()
            logger.info(f"Successfully updated forecast for product_id={product_id}")

        except Exception as e:
            logger.error(f"Error in background forecast generation for product_id={product_id}: {str(e)}")


# In-memory set to track currently generating forecasts to prevent duplicate concurrent API calls
_generating_forecasts = set()
_generating_lock = threading.Lock()

def trigger_forecast_generation(app, product_id, sales_data, projection_size=9, sample_size=None):
    """
    Triggers the forecast generation in a background thread.
    """
    with _generating_lock:
        if product_id in _generating_forecasts:
            logger.info(f"Forecast generation already in progress for product_id={product_id}. Skipping.")
            return
        _generating_forecasts.add(product_id)

    # If app is a LocalProxy (e.g. current_app), get the underlying object.
    # If it's already the Flask app, this might fail, so we handle it.
    try:
        app_obj = app._get_current_object()
    except AttributeError:
        app_obj = app

    def wrapper():
        try:
            generate_forecast_background(app_obj, product_id, sales_data, projection_size, sample_size)
        finally:
            with _generating_lock:
                _generating_forecasts.discard(product_id)

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()
