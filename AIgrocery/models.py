from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.String(20), nullable=False) # YYYY-MM-DD
    nutrition_value = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(50), nullable=True, default="Pantry")
    image_url = db.Column(db.String(500), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'expiry_date': self.expiry_date,
            'nutrition_value': self.nutrition_value,
            'price': self.price,
            'category': self.category,
            'image_url': self.image_url
        }

class MealPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(100), nullable=False)
    suggestions = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    store = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    measurement = db.Column(db.String(50), nullable=True)
    store = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    badge = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=True, default="Grocery")
    image_url = db.Column(db.String(500), nullable=True)
    prices_json = db.Column(db.Text, nullable=True) # JSON encoding logic for store prices

    def to_dict(self):
        import json
        prices = {}
        if self.prices_json:
            try: prices = json.loads(self.prices_json)
            except: pass
            
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "measurement": self.measurement,
            "store": self.store,
            "price": self.price,
            "prices": prices,
            "badge": self.badge,
            "category": self.category,
            "image_url": self.image_url
        }

class PurchaseHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.Integer, default=1)
    last_purchased = db.Column(db.DateTime, default=datetime.utcnow)
