import unittest
from config import Config
Config.DATABASE_URL = 'sqlite:///:memory:'

from app import create_app
from database import db
from models import Product

class TestNepCompareAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Seed test product
            p = Product(
                name="Test Laptop Pro",
                normalized_name="test laptop pro",
                price=50000.0,
                store="Hukut",
                product_url="https://test.com/p1",
                availability="In Stock"
            )
            db.session.add(p)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_homepage_status(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_api_products(self):
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['items'][0]['name'], "Test Laptop Pro")

    def test_api_search(self):
        response = self.client.get('/api/search?q=laptop')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total'], 1)

if __name__ == '__main__':
    unittest.main()
