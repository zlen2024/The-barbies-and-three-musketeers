import os
import json
import logging
from datetime import datetime
import pandas as pd
from flask import current_app

logger = logging.getLogger(__name__)

def generate_margin_simulation(product_id, sales_data, proposed_price, volume_discount_pct):
    """
    Run forecast generation using the Nixtla SDK to predict demand based on a proposed price.
    `sales_data` should be a list of dicts: [{'unique_id': str, 'timestamp': 'YYYY-MM-01', 'value': 123.4, 'price': 100.0}, ...]
    `product_id` is the ID of the product.
    `proposed_price` is the hypothetical price.
    `volume_discount_pct` is the volume discount percentage (0-100).
    """
    try:
        api_key = os.environ.get('AZURE_TIMEGEN_API_KEY')
        if not api_key:
            logger.error("AZURE_TIMEGEN_API_KEY not found in environment.")
            return {"error": "AZURE_TIMEGEN_API_KEY not found in environment."}

        from nixtla import NixtlaClient

        # Initialize client with Azure endpoint
        client = NixtlaClient(
            base_url="https://TimeGEN-1-ChinHin.eastus2.models.ai.azure.com",
            api_key=api_key
        )

        if not sales_data:
            logger.warning(f"No sales data provided for product_id={product_id}")
            return {"error": "No sales data provided."}

        # Prepare dataframe
        df = pd.DataFrame(sales_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Create exogenous data for the forecast horizon (next 4 weeks)
        future_dates = pd.date_range(start=df['timestamp'].max() + pd.Timedelta(days=7), periods=4, freq='7D')

        # Assume unique_id is the same for all historical rows
        unique_id = df['unique_id'].iloc[0]

        future_exog = pd.DataFrame({
            'unique_id': [unique_id] * 4,
            'timestamp': future_dates,
            'price': [proposed_price] * 4
        })

        # Generate forecast for the next 4 weeks
        # We pass future_exog as X_df to the client.forecast method
        timegen_fcst_df = client.forecast(
            df=df,
            h=4,
            freq='7D',
            time_col='timestamp',
            target_col='value',
            X_df=future_exog
        )

        # Process the result
        forecast_results = []

        # Find the prediction column (anything other than timestamp and unique_id)
        pred_col = None
        for col in timegen_fcst_df.columns:
            if col not in ['timestamp', 'unique_id']:
                pred_col = col
                break

        if not pred_col:
            logger.error("No prediction column returned from TimeGEN API.")
            return {"error": "No prediction column returned from TimeGEN API."}

        total_predicted_volume = 0
        for index, row in timegen_fcst_df.iterrows():
            pred_value = row.get(pred_col, 0)

            if pd.isna(pred_value):
                pred_value = 0

            # Calculate discounted subtotal
            # The pred_value is the raw predicted subtotal
            raw_subtotal = max(0, float(pred_value)) # Prevent negative forecasts
            discounted_subtotal = raw_subtotal * (1 - (volume_discount_pct / 100.0))

            # Calculate quantity based on proposed price
            quantity = 0
            if proposed_price > 0:
                quantity = discounted_subtotal / proposed_price

            # We format it to YYYY-MM-DD for weekly data
            week_str = row['timestamp'].strftime("%Y-%m-%d")

            forecast_results.append({
                "date": week_str,
                "subtotal": discounted_subtotal,
                "quantity": quantity,
                "price": proposed_price
            })
            total_predicted_volume += quantity

        return {
            "success": True,
            "forecast": forecast_results,
            "total_volume": total_predicted_volume
        }

    except Exception as e:
        logger.error(f"Error in margin simulation for product_id={product_id}: {str(e)}")
        return {"error": str(e)}
