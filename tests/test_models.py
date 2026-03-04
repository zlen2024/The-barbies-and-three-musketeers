import sys
from unittest.mock import MagicMock

# Mocking flask dependencies
mock_flask_sqlalchemy = MagicMock()
mock_flask_login = MagicMock()

class MockModel:
    pass

class MockUserMixin:
    pass

db = MagicMock()
db.Model = MockModel
db.Column = MagicMock()
db.Integer = MagicMock()
db.String = MagicMock()
db.ForeignKey = MagicMock()
db.DateTime = MagicMock()
db.Boolean = MagicMock()
db.Float = MagicMock()
db.Text = MagicMock()
db.relationship = MagicMock()
db.backref = MagicMock()

mock_flask_sqlalchemy.SQLAlchemy.return_value = db
mock_flask_login.UserMixin = MockUserMixin

sys.modules["flask_sqlalchemy"] = mock_flask_sqlalchemy
sys.modules["flask_login"] = mock_flask_login

import unittest
# Now we can safely import from models
from models import Product

class TestProductModel(unittest.TestCase):
    def test_total_stock_no_locations(self):
        """Test Product.total_stock when there are no ProductLoc entries."""
        product = Product()
        product.product_locs = []

        self.assertEqual(product.total_stock, 0, "Total stock should be 0 when no locations exist.")

    def test_total_stock_multiple_locations(self):
        """Test Product.total_stock sums quantity_on_hand from all ProductLoc entries."""
        pl1 = MagicMock()
        pl1.quantity_on_hand = 10

        pl2 = MagicMock()
        pl2.quantity_on_hand = 25

        pl3 = MagicMock()
        pl3.quantity_on_hand = 5

        product = Product()
        product.product_locs = [pl1, pl2, pl3]

        self.assertEqual(product.total_stock, 40, "Total stock should be 40.")

    def test_total_stock_single_location(self):
        """Test Product.total_stock with a single location."""
        pl = MagicMock()
        pl.quantity_on_hand = 100
        product = Product()
        product.product_locs = [pl]

        self.assertEqual(product.total_stock, 100, "Total stock should be 100.")

if __name__ == "__main__":
    unittest.main()
