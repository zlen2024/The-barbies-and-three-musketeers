import unittest
from unittest.mock import MagicMock, patch
import sys
import time

# Mock external dependencies
sys.modules['nixtla'] = MagicMock()
sys.modules['pandas'] = MagicMock()

import azure_forecast

class TestAzureForecast(unittest.TestCase):
    def test_concurrency_lock(self):
        app_mock = MagicMock()

        # We need to simulate a long running task so we can check the set
        def mock_generate(*args):
            time.sleep(0.5)

        with patch('azure_forecast.generate_forecast_background', side_effect=mock_generate):
            # First call should start execution
            azure_forecast.trigger_forecast_generation(app_mock, 1, [])

            # Wait a tiny bit for the thread to start
            time.sleep(0.1)

            # Simulated lock check (in-memory state)
            self.assertIn(1, azure_forecast._generating_forecasts)

            # Second concurrent call should skip
            azure_forecast.trigger_forecast_generation(app_mock, 1, [])

            # Ensure it is still in the set
            self.assertIn(1, azure_forecast._generating_forecasts)

            # Wait for the first thread to finish
            time.sleep(0.5)

        self.assertNotIn(1, azure_forecast._generating_forecasts)

if __name__ == '__main__':
    unittest.main()
