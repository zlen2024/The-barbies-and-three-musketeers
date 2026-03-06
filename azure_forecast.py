import os
import json
import logging
import threading
from datetime import datetime, timedelta
import pandas as pd

from models import db, Forecast

logger = logging.getLogger(__name__)

def generate_forecast_background(app, product_id, sales_data):
    """
    Run forecast generation in background using the Nixtla SDK.
    `sales_data` should be a list of dicts: [{'timestamp': 'YYYY-MM-01', 'value': 123.4}, ...]
    `product_id` is the ID of the product, or None for system-wide.
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

            # Generate forecast for the next 2 months
            timegen_fcst_df = client.forecast(
                df=df,
                h=2,
                freq='MS',
                time_col='timestamp',
                target_col='value'
            )

            # Process the result
            forecast_results = []
            for index, row in timegen_fcst_df.iterrows():
                # 'TimeGPT' is the default column name for Nixtla forecasts
                pred_value = row.get('TimeGPT', row.get('value', 0))
                # Fallback to sum of historical average if Nixtla fails in some way
                if pd.isna(pred_value):
                    pred_value = 0

                # We format it to YYYY-MM
                month_str = row['timestamp'].strftime("%Y-%m")
                forecast_results.append({
                    "month": month_str,
                    "value": max(0, float(pred_value)) # Prevent negative forecasts
                })

            # Save to database
            forecast = Forecast.query.filter_by(product_id=product_id).first()
            if not forecast:
                forecast = Forecast(product_id=product_id)
                db.session.add(forecast)

            forecast.forecast_data = json.dumps(forecast_results)
            forecast.last_updated = datetime.utcnow()

            # Simple projected demand is sum of forecast
            forecast.projected_demand = int(sum([f['value'] for f in forecast_results]))

            db.session.commit()
            logger.info(f"Successfully updated forecast for product_id={product_id}")

        except Exception as e:
            logger.error(f"Error in background forecast generation for product_id={product_id}: {str(e)}")


def trigger_forecast_generation(app, product_id, sales_data):
    """
    Triggers the forecast generation in a background thread.
    """
    thread = threading.Thread(target=generate_forecast_background, args=(app._get_current_object(), product_id, sales_data))
    thread.daemon = True
    thread.start()
