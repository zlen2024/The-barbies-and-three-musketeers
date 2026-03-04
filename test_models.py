import sys
from unittest.mock import MagicMock
sys.modules['flask_sqlalchemy'] = MagicMock()
sys.modules['flask_login'] = MagicMock()
from models import *
print('Models OK')
