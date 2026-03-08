import os
import json
import logging
import threading
from datetime import datetime, timedelta
import pandas as pd

from models import db, Forecast, FinetunedModel

logger = logging.getLogger(__name__)

def finetune_model_background(app, sales_data):
    """
    Run fine-tuning in background using the Nixtla SDK.
    `sales_data` is system-wide sales data.
    """
    with app.app_context():
        # Insert a pending FinetunedModel record immediately
        new_finetuned_model = FinetunedModel(status='pending')
        db.session.add(new_finetuned_model)
        db.session.commit()

        try:
            logger.info("Starting background fine-tuning")
            api_key = os.environ.get('AZURE_TIMEGEN_API_KEY')
            if not api_key:
                logger.error("AZURE_TIMEGEN_API_KEY not found in environment.")
                new_finetuned_model.status = 'failed'
                db.session.commit()
                return

            from nixtla import NixtlaClient

            client = NixtlaClient(
                base_url="https://TimeGEN-1-ChinHin.eastus2.models.ai.azure.com",
                api_key=api_key
            )

            if not sales_data:
                logger.warning("No sales data provided for fine-tuning")
                new_finetuned_model.status = 'failed'
                db.session.commit()
                return

            # Find and delete old models before creating the new one
            old_models = FinetunedModel.query.filter(FinetunedModel.id != new_finetuned_model.id).all()
            for old_model in old_models:
                if old_model.model_id:
                    try:
                        logger.info(f"Deleting old fine-tuned model {old_model.model_id} from Nixtla")
                        client.delete_finetuned_model(old_model.model_id)
                    except Exception as delete_e:
                        logger.warning(f"Failed to delete old model {old_model.model_id} from Nixtla: {delete_e}")
                db.session.delete(old_model)
            db.session.commit()

            df = pd.DataFrame(sales_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp')

            # Run fine-tuning
            logger.info("Calling Nixtla finetune()...")
            # For univariate, finetune expects a unique_id column. If not provided, it assumes one series.
            # However, typically you need df to be format matching what `forecast` takes.
            if 'unique_id' not in df.columns:
                 df.insert(0, 'unique_id', 'global')

            # We can use client.finetune as per docs
            # finetune(df=df, h=9, finetune_steps=10, time_col='timestamp', target_col='value')
            output_model_id = client.finetune(
                df=df,
                h=9,
                finetune_steps=10,
                time_col='timestamp',
                target_col='value'
            )

            logger.info(f"Fine-tuning successful, model_id: {output_model_id}")
            new_finetuned_model.model_id = output_model_id
            new_finetuned_model.status = 'ready'
            db.session.commit()

        except Exception as e:
            logger.error(f"Error in background fine-tuning: {str(e)}")
            new_finetuned_model.status = 'failed'
            db.session.commit()

# In-memory set to track currently generating finetuning
_finetuning_lock = threading.Lock()
_is_finetuning = False

def trigger_finetune_generation(app, sales_data):
    """
    Triggers the global fine-tuning generation in a background thread.
    """
    global _is_finetuning
    with _finetuning_lock:
        if _is_finetuning:
            logger.info("Fine-tuning already in progress. Skipping.")
            return
        _is_finetuning = True

    try:
        app_obj = app._get_current_object()
    except AttributeError:
        app_obj = app

    def wrapper():
        global _is_finetuning
        try:
            finetune_model_background(app_obj, sales_data)
        finally:
            with _finetuning_lock:
                _is_finetuning = False

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()


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

            # Check for a ready fine-tuned model
            latest_model = FinetunedModel.query.filter_by(status='ready').order_by(FinetunedModel.created_at.desc()).first()

            # Generate forecast for the next 9 weeks
            forecast_kwargs = {
                'df': df,
                'h': 9,
                'freq': '7D',
                'time_col': 'timestamp',
                'target_col': 'value'
            }

            if latest_model and latest_model.model_id:
                logger.info(f"Using fine-tuned model {latest_model.model_id} for forecast")
                forecast_kwargs['finetuned_model_id'] = latest_model.model_id

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
