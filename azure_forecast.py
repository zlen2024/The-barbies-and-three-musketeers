import os
import json
import logging
import threading
from datetime import datetime, timedelta
import pandas as pd

from models import db, Forecast, FinetunedModel

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

            # Check if there is a ready finetuned model
            finetuned_model = FinetunedModel.query.filter_by(status='ready').first()
            forecast_kwargs = {
                'df': df,
                'h': 9,
                'freq': '7D',
                'time_col': 'timestamp',
                'target_col': 'value'
            }
            if finetuned_model:
                logger.info(f"Using finetuned model: {finetuned_model.model_id} for forecasting")
                forecast_kwargs['finetuned_model_id'] = finetuned_model.model_id

            # Generate forecast for the next 9 weeks
            timegen_fcst_df = client.forecast(**forecast_kwargs)

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


_finetuning_in_progress = False
_finetuning_lock = threading.Lock()

def is_finetuning_in_progress():
    global _finetuning_in_progress
    with _finetuning_lock:
        return _finetuning_in_progress

def generate_finetune_background(app, sales_data):
    """
    Run finetuning in background using Nixtla SDK.
    `sales_data` should be a list of dicts: [{'timestamp': 'YYYY-MM-01', 'value': 123.4}, ...]
    """
    global _finetuning_in_progress
    with app.app_context():
        try:
            logger.info(f"Starting background finetuning")
            api_key = os.environ.get('AZURE_TIMEGEN_API_KEY')
            if not api_key:
                logger.error("AZURE_TIMEGEN_API_KEY not found in environment.")
                return

            from nixtla import NixtlaClient
            client = NixtlaClient(
                base_url="https://TimeGEN-1-ChinHin.eastus2.models.ai.azure.com",
                api_key=api_key
            )

            if not sales_data:
                logger.warning(f"No sales data provided for finetuning")
                return

            df = pd.DataFrame(sales_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp')

            # Delete old model if it exists
            old_model = FinetunedModel.query.filter_by(status='ready').first()
            if old_model:
                try:
                    logger.info(f"Deleting old finetuned model: {old_model.model_id}")
                    client.delete_finetuned_model(old_model.model_id)
                except Exception as e:
                    logger.warning(f"Failed to delete old model from Nixtla: {e}")
                db.session.delete(old_model)
                db.session.commit()

            # Create pending record
            new_model_record = FinetunedModel(model_id='pending_id', status='pending')
            db.session.add(new_model_record)
            db.session.commit()

            # Trigger Finetune
            # Reusing the existing forecast parameters structure with finetune enabled
            model_id = client.finetune(
                df=df,
                h=9,
                freq='7D',
                time_col='timestamp',
                target_col='value',
                finetune_steps=10
            )

            logger.info(f"Successfully generated finetuned model with ID: {model_id}")

            new_model_record.model_id = model_id
            new_model_record.status = 'ready'
            db.session.commit()

        except Exception as e:
            logger.error(f"Error in background finetuning: {str(e)}")
            pending_model = FinetunedModel.query.filter_by(status='pending').first()
            if pending_model:
                pending_model.status = 'failed'
                db.session.commit()
        finally:
            with _finetuning_lock:
                _finetuning_in_progress = False

def trigger_finetune_generation(app, sales_data):
    """
    Triggers the finetune generation in a background thread.
    """
    global _finetuning_in_progress
    with _finetuning_lock:
        if _finetuning_in_progress:
            logger.info("Finetuning generation already in progress. Skipping.")
            return
        _finetuning_in_progress = True

    try:
        app_obj = app._get_current_object()
    except AttributeError:
        app_obj = app

    def wrapper():
        generate_finetune_background(app_obj, sales_data)

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()

# In-memory set to track currently generating forecasts to prevent duplicate concurrent API calls
_generating_forecasts = set()
_generating_lock = threading.Lock()

def trigger_forecast_generation(app, product_id, sales_data):
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
            generate_forecast_background(app_obj, product_id, sales_data)
        finally:
            with _generating_lock:
                _generating_forecasts.discard(product_id)

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()
