from app import app
from models import db, PantryItem, CartItem
import json
import agents
from datetime import datetime, timedelta

with app.app_context():
    # 1. Clear existing
    PantryItem.query.delete()
    CartItem.query.delete()
    db.session.commit()

    # 2. Add realistic Pantry Items (matching categories)
    pantry = [
        # FRESH PRODUCE
        PantryItem(name="Tomato", quantity=10, expiry_date=(datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Vitamins", price=40.0),
        PantryItem(name="Onion", quantity=15, expiry_date=(datetime.utcnow() + timedelta(days=15)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Minerals", price=35.0),
        PantryItem(name="Potato", quantity=20, expiry_date=(datetime.utcnow() + timedelta(days=20)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Carbs", price=50.0),
        PantryItem(name="Carrot", quantity=8, expiry_date=(datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Vitamin A", price=45.0),
        PantryItem(name="Spinach", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Iron", price=30.0),
        PantryItem(name="Broccoli", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Fiber", price=90.0),
        PantryItem(name="Capsicum", quantity=4, expiry_date=(datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Antioxidants", price=60.0),
        PantryItem(name="Apple", quantity=6, expiry_date=(datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Fiber", price=120.0),
        PantryItem(name="Banana", quantity=12, expiry_date=(datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Potassium", price=50.0),
        PantryItem(name="Orange", quantity=6, expiry_date=(datetime.utcnow() + timedelta(days=8)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Vitamin C", price=100.0),
        PantryItem(name="Mango", quantity=4, expiry_date=(datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Sugar", price=150.0),
        PantryItem(name="Grapes", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Antioxidants", price=80.0),

        # DAIRY & ESSENTIALS
        PantryItem(name="Milk", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Calcium", price=65.0),
        PantryItem(name="Butter", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Fat", price=55.0),
        PantryItem(name="Cheese", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=20)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Protein", price=120.0),
        PantryItem(name="Curd (Yogurt)", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Probiotics", price=40.0),
        PantryItem(name="Paneer", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Protein", price=85.0),
        PantryItem(name="Eggs", quantity=12, expiry_date=(datetime.utcnow() + timedelta(days=15)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Protein", price=84.0),
        PantryItem(name="Bread", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d'), category="Bakery", nutrition_value="Carbs", price=40.0),
        PantryItem(name="Cooking Oil", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Fat", price=150.0),
        PantryItem(name="Sugar", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Carbs", price=45.0),
        PantryItem(name="Salt", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Sodium", price=25.0),

        # GRAINS & STAPLES
        PantryItem(name="Rice", quantity=5, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Carbs", price=300.0),
        PantryItem(name="Wheat Flour (Atta)", quantity=5, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Carbs", price=250.0),
        PantryItem(name="Pasta", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Carbs", price=60.0),
        PantryItem(name="Noodles", quantity=4, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Carbs", price=50.0),
        PantryItem(name="Oats", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Fiber", price=150.0),
        PantryItem(name="Lentils (Dal)", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Protein", price=120.0),
        PantryItem(name="Chickpeas", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Protein", price=90.0),
        PantryItem(name="Kidney Beans (Rajma)", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Protein", price=110.0),

        # FROZEN FOODS
        PantryItem(name="Frozen Peas", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Frozen", nutrition_value="Vitamins", price=120.0),
        PantryItem(name="Frozen Corn", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Frozen", nutrition_value="Carbs", price=110.0),
        PantryItem(name="Frozen French Fries", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Frozen", nutrition_value="Fat", price=150.0),
        PantryItem(name="Frozen Chicken Nuggets", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=60)).strftime('%Y-%m-%d'), category="Frozen", nutrition_value="Protein", price=250.0),
        PantryItem(name="Frozen Mixed Vegetables", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Frozen", nutrition_value="Vitamins", price=140.0),

        # QUICK MEALS / READY ITEMS
        PantryItem(name="Instant Noodles", quantity=5, expiry_date=(datetime.utcnow() + timedelta(days=120)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Carbs", price=60.0),
        PantryItem(name="Ready-to-eat Pasta", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=120)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Carbs", price=90.0),
        PantryItem(name="Soup Packets", quantity=4, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Sodium", price=60.0),
        PantryItem(name="Breakfast Cereals", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Fiber", price=250.0),
        PantryItem(name="Peanut Butter", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Protein", price=180.0),
        PantryItem(name="Jam", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Sugar", price=120.0),

        # PROTEIN ITEMS
        PantryItem(name="Chicken Breast", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Protein", price=280.0),
        PantryItem(name="Fish", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Omega-3", price=320.0),
        PantryItem(name="Tofu", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Protein", price=100.0),

        # SNACKS
        PantryItem(name="Biscuits", quantity=3, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Carbs", price=40.0),
        PantryItem(name="Chips", quantity=4, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Fat", price=80.0),
        PantryItem(name="Chocolates", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Sugar", price=100.0),
        PantryItem(name="Energy Bars", quantity=5, expiry_date=(datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Protein", price=200.0),
        PantryItem(name="Dry Fruits", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Nutrients", price=450.0),
        
        # INDIAN ESSENTIALS - FRESH
        PantryItem(name="Coriander (Dhaniya)", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Vitamins", price=20.0),
        PantryItem(name="Curry Leaves", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Flavor", price=10.0),
        PantryItem(name="Green Chilli", quantity=10, expiry_date=(datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Vitamin C", price=15.0),
        PantryItem(name="Ginger", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=15)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Digestion", price=25.0),
        PantryItem(name="Garlic", quantity=5, expiry_date=(datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d'), category="Fresh", nutrition_value="Immunity", price=30.0),

        # INDIAN ESSENTIALS - DAIRY
        PantryItem(name="Paneer", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Protein", price=90.0),
        PantryItem(name="Curd (Dahi)", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Probiotics", price=45.0),
        PantryItem(name="Ghee", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Dairy", nutrition_value="Healthy Fats", price=550.0),

        # INDIAN ESSENTIALS - STAPLES
        PantryItem(name="Basmati Rice", quantity=5, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Carbs", price=500.0),
        PantryItem(name="Atta (Wheat Flour)", quantity=10, expiry_date=(datetime.utcnow() + timedelta(days=120)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Carbs", price=400.0),
        PantryItem(name="Toor Dal", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Protein", price=160.0),
        PantryItem(name="Moong Dal", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Protein", price=140.0),
        PantryItem(name="Chana Dal", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=180)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Protein", price=130.0),

        # INDIAN ESSENTIALS - SPICES
        PantryItem(name="Turmeric Powder", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Antiseptic", price=50.0),
        PantryItem(name="Red Chilli Powder", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Spice", price=60.0),
        PantryItem(name="Garam Masala", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Aroma", price=80.0),
        PantryItem(name="Cumin Seeds (Jeera)", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Digestion", price=70.0),
        PantryItem(name="Mustard Seeds (Rai)", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d'), category="Grocery", nutrition_value="Flavor", price=40.0),

        # INDIAN ESSENTIALS - READY/QUICK
        PantryItem(name="Pav Bread", quantity=2, expiry_date=(datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d'), category="Bakery", nutrition_value="Carbs", price=40.0),
        PantryItem(name="Instant Poha", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=120)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Carbs", price=60.0),
        PantryItem(name="Upma Mix", quantity=1, expiry_date=(datetime.utcnow() + timedelta(days=120)).strftime('%Y-%m-%d'), category="Snacks", nutrition_value="Carbs", price=70.0)
    ]
    for p in pantry: 
        p.image_url = agents.get_image_url(p.name, p.category)
        db.session.add(p)

    # 3. Add CartItems with JSON pricing arrays and measurements
    cart = [
        CartItem(
            name="Organic Spinach",
            measurement="500g",
            store="DMart",
            price=45.0,
            badge="Healthier Option",
            category="Fresh",
            prices_json=json.dumps({"Instamart": 55.0, "BigBasket": 60.0, "DMart": 45.0})
        ),
        CartItem(
            name="Whole Wheat Bread",
            measurement="1 Loaf",
            store="Instamart",
            price=40.0,
            badge="Cheapest Found",
            category="Fresh",
            prices_json=json.dumps({"Instamart": 40.0, "BigBasket": 45.0, "DMart": 42.0})
        ),
        CartItem(
            name="Almond Milk",
            measurement="1 Litre",
            store="BigBasket",
            price=120.0,
            badge="Healthier Option",
            category="Dairy",
            prices_json=json.dumps({"Instamart": 130.0, "BigBasket": 120.0, "DMart": 125.0})
        ),
        CartItem(
            name="Frozen Mixed Berries",
            measurement="400g",
            store="DMart",
            price=250.0,
            badge="Best Deal",
            category="Frozen",
            prices_json=json.dumps({"Instamart": 280.0, "BigBasket": 270.0, "DMart": 250.0})
        )
    ]
    for c in cart: 
        c.image_url = agents.get_image_url(c.name, c.category)
        db.session.add(c)

    db.session.commit()
    print("Database seeded with mock items successfully!")
