import sys
from unittest.mock import MagicMock
sys.modules['nixtla'] = MagicMock()
sys.modules['pandas'] = MagicMock()
from azure_forecast import trigger_forecast_generation
print("Import successful")
