import pandas as pd
from nixtla import NixtlaClient
import os

api_key = os.environ.get('AZURE_TIMEGEN_API_KEY', 'dummy')
client = NixtlaClient(
    base_url="https://TimeGEN-1-ChinHin.eastus2.models.ai.azure.com",
    api_key=api_key
)

df = pd.DataFrame({
    'timestamp': pd.date_range('2023-01-01', periods=100),
    'value': range(100)
})

try:
    client.finetune(df=df, finetune_steps=10, finetune_depth=3, time_col='timestamp', target_col='value')
except Exception as e:
    print(e)
