import os
from nixtla import NixtlaClient
api_key = os.environ.get('AZURE_TIMEGEN_API_KEY', 'dummy')
client = NixtlaClient(
    base_url="https://TimeGEN-1-ChinHin.eastus2.models.ai.azure.com",
    api_key=api_key
)
try:
    print(client.finetune)
except Exception as e:
    print(f"Error type: {type(e)}")
    print(f"Error msg: {e}")
