import os, requests, json
from dotenv import load_dotenv
# Load environment variables FIRST
load_dotenv()

from flask import Flask, render_template, jsonify, request
from models import db, PantryItem, MealPlan, PriceHistory, MessageHistory, CartItem, PurchaseHistory
from datetime import datetime, timedelta
import agents

app = Flask(__name__)
# Configure SQLite DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pantry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.before_request
def create_tables():
    if not hasattr(app, 'tables_created'):
        db.create_all()
        app.tables_created = True

@app.route('/')
def index():
    return render_template('index.html')

# --- RECEIPT & PANTRY API ---

@app.route('/api/pantry', methods=['GET'])
def get_pantry():
    items = PantryItem.query.all()
    pantry_list = []
    for item in items:
        pantry_list.append(item.to_dict())
    return jsonify(pantry_list)

@app.route('/api/ingest_receipt', methods=['POST'])
def ingest_receipt():
    data = request.json
    receipt_text = data.get('receipt_text', '')
    
    extracted_items = agents.simulate_receipt_parsing(receipt_text)
    
    added_count = 0
    for item in extracted_items:
        expiry_date = (datetime.utcnow() + timedelta(days=item['expiry_days'])).strftime('%Y-%m-%d')
        new_item = PantryItem(
            name=item['name'],
            quantity=item['quantity'],
            expiry_date=expiry_date,
            nutrition_value="Calculated Macros",
            category=item.get('category', 'Pantry'),
            image_url=item.get('image_url') or agents.get_image_url(item['name'], item.get('category'))
        )
        db.session.add(new_item)
        
        freq_item = PurchaseHistory.query.filter_by(item_name=item['name']).first()
        if freq_item:
            freq_item.frequency += 1
            freq_item.last_purchased = datetime.utcnow()
        else:
            new_freq = PurchaseHistory(item_name=item['name'], frequency=1)
            db.session.add(new_freq)
            
        added_count += 1
        
    db.session.commit()
    return jsonify({"message": f"Successfully parsed receipt! Auto-added {added_count} items.", "items_added": added_count}), 200

# --- CHATBOT API ---

@app.route('/api/chat', methods=['POST'])
def send_chat_message():
    data = request.json
    user_text = data.get('text', '')
    pantry_items = PantryItem.query.all()
    
    bot_response_text = agents.chatbot_response(user_text, pantry_items)
    
    # Handle Special Triggers
    if bot_response_text.startswith("RENDER_RECIPE_CARD_MANUAL"):
        dish = bot_response_text.split(":")[1]
        recipe = agents.generate_recipe("manual", dish, pantry_items)
        return jsonify({"reply": "", "recipe": recipe}), 200
        
    elif bot_response_text == "RENDER_RECIPE_PANTRY":
        # Get multiple suggestions as requested (2-3 meals)
        recipes = agents.generate_recipe("cart_recipes", "healthy meals", pantry_items)
        return jsonify({"reply": "I've found a few great meal options you can make using your pantry items:", "recipes": recipes}), 200
        
    elif bot_response_text == "RENDER_RECIPE_CART":
        cart_items = CartItem.query.all()
        # Return multiple recipes
        recipes = agents.generate_recipe("cart_recipes", "auto", pantry_items, cart_items)
        return jsonify({"reply": "Here are some recipes using items from your cart and pantry:", "recipes": recipes}), 200
        
    elif bot_response_text.startswith("ADD_TO_CART_TRIGGERED:"):
        items_str = bot_response_text.split(":", 1)[1]
        needed = [i.strip() for i in items_str.split(",") if i.strip()]
        if not needed:
            needed = ["Olive Oil", "Mozzarella Cheese"] # Fallback
        optimized_items = agents.generate_optimized_cart(needed)
        for i in optimized_items:
            ci = CartItem(name=i['name'], store=i['store'], price=i['price'], badge=i['badge'], category=i.get('category', 'Grocery'))
            db.session.add(ci)
        db.session.commit()
        return jsonify({"reply": f"I've carefully added the following items to your cart: {', '.join(needed)}, with optimized prices!"}), 200

    return jsonify({"reply": bot_response_text}), 200

# --- PLANNER & CART API ---

@app.route('/api/planner', methods=['POST'])
def generate_meal_plan():
    data = request.json
    goal = data.get('goal', 'balanced')
    pantry_items = PantryItem.query.all()
    recipe = agents.generate_recipe("planner", goal, pantry_items)
    return jsonify({"recipe": recipe})

@app.route('/api/cart', methods=['GET'])
def get_cart():
    items = CartItem.query.all()
    needs_commit = False
    for item in items:
        if not item.image_url:
            item.image_url = agents.get_image_url(item.name, item.category)
            needs_commit = True
    if needs_commit:
        db.session.commit()

    cart_list = [item.to_dict() for item in items]
    
    stores = ["Instamart", "BigBasket", "DMart"]
    store_totals = { s: 0.0 for s in stores }
    
    for item in items:
        prices = {}
        if item.prices_json:
            try: prices = json.loads(item.prices_json)
            except: pass
            
        for s in stores:
            store_totals[s] += prices.get(s, item.price)
            
    best_store = min(store_totals, key=store_totals.get) if store_totals else "Instamart"
    max_total = max(store_totals.values()) if store_totals else 0.0
    best_total = store_totals[best_store] if store_totals else 0.0
    savings = max_total - best_total
    
    total = sum([i.price for i in items])
    return jsonify({
        "cart": cart_list, 
        "total_cost": round(total, 2),
        "store_totals": {k: round(v, 2) for k, v in store_totals.items()},
        "best_store": best_store,
        "savings": round(savings, 2)
    })

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    item_name = data.get('name')
    # Duplicate check: increment quantity if item already in cart
    existing = CartItem.query.filter(CartItem.name.ilike(item_name)).first()
    if existing:
        existing.quantity = (existing.quantity or 1) + 1
        db.session.commit()
        return jsonify(existing.to_dict()), 200
    opt = agents.generate_optimized_cart([item_name])[0]
    ci = CartItem(
        name=opt['name'],
        quantity=1,
        measurement=opt.get('measurement', '1 Pack'),
        store=opt['store'],
        price=opt['price'],
        badge=opt['badge'],
        category=opt.get('category', 'Grocery'),
        image_url=opt.get('image_url') or agents.get_image_url(opt['name'], opt.get('category')),
        prices_json=json.dumps(opt.get('prices', {}))
    )
    db.session.add(ci)
    db.session.commit()
    return jsonify(ci.to_dict()), 201

@app.route('/api/cart/missing', methods=['POST'])
def add_missing_to_cart():
    data = request.json
    missing_items = data.get('missing_items', [])
    # Filter out items already in cart
    existing_names = {c.name.lower() for c in CartItem.query.all()}
    new_items = [i for i in missing_items if i.lower() not in existing_names]
    if not new_items:
        return jsonify({"message": "All items are already in the cart."}), 200
    opt_items = agents.generate_optimized_cart(new_items)
    for opt in opt_items:
        ci = CartItem(
            name=opt['name'],
            quantity=1,
            measurement=opt.get('measurement', '1 Pack'),
            store=opt['store'],
            price=opt['price'],
            badge=opt['badge'],
            category=opt.get('category', 'Grocery'),
            prices_json=json.dumps(opt.get('prices', {}))
        )
        db.session.add(ci)
    db.session.commit()
    return jsonify({"message": f"Added {len(new_items)} new item(s) to cart."}), 201

@app.route('/api/cart/<int:item_id>/quantity', methods=['PATCH'])
def update_cart_quantity(item_id):
    data = request.json
    action = data.get('action')  # 'increase' or 'decrease'
    item = CartItem.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404
    if action == 'increase':
        item.quantity = (item.quantity or 1) + 1
        db.session.commit()
        return jsonify(item.to_dict()), 200
    elif action == 'decrease':
        if (item.quantity or 1) <= 1:
            db.session.delete(item)
            db.session.commit()
            return jsonify({"deleted": True}), 200
        else:
            item.quantity -= 1
            db.session.commit()
            return jsonify(item.to_dict()), 200
    return jsonify({"message": "Invalid action"}), 400

@app.route('/api/cart/checkout_store', methods=['POST'])
def checkout_store():
    data = request.json
    target_store = data.get('store')
    items = CartItem.query.all()
    for item in items:
        if item.prices_json:
            try:
                prices = json.loads(item.prices_json)
                if target_store in prices:
                    item.store = target_store
                    item.price = prices[target_store]
            except: pass
    db.session.commit()
    return jsonify({"message": f"Successfully switched cart to {target_store}"}), 200

@app.route('/api/cart/switch_item', methods=['POST'])
def switch_item_store():
    data = request.json
    item_id = data.get('item_id')
    target_store = data.get('store')
    item = CartItem.query.get(item_id)
    if item and item.prices_json:
        try:
            prices = json.loads(item.prices_json)
            if target_store in prices:
                item.store = target_store
                item.price = prices[target_store]
                db.session.commit()
        except: pass
    return jsonify({"message": "Switched item successfully."}), 200

@app.route('/api/cart/checkout', methods=['POST'])
def checkout():
    cart_items = CartItem.query.all()
    if not cart_items:
        return jsonify({"message": "Your cart is empty!"}), 400

    today = datetime.utcnow()
    added_count = 0

    # Smart expiry logic based on category
    def get_expiry_days(category):
        cat = (category or "").lower()
        if "fresh" in cat:       return 4   # Fresh: 3-5 days
        if "dairy" in cat:       return 6   # Dairy: 5-7 days
        if "frozen" in cat:      return 25  # Frozen: 20-30 days
        return 60                            # Packaged/Grocery: 30-90 days

    for cart_item in cart_items:
        expiry_days = get_expiry_days(cart_item.category)
        expiry_date = (today + timedelta(days=expiry_days)).strftime('%Y-%m-%d')

        # Duplicate prevention: increase quantity if item already exists
        existing = PantryItem.query.filter(
            PantryItem.name.ilike(cart_item.name)
        ).first()

        if existing:
            existing.quantity += 1
        else:
            new_pantry_item = PantryItem(
                name=cart_item.name,
                quantity=1,
                expiry_date=expiry_date,
                category=cart_item.category or "Grocery",
                nutrition_value="Verified",
                price=cart_item.price,
                image_url=cart_item.image_url or agents.get_image_url(cart_item.name, cart_item.category)
            )
            db.session.add(new_pantry_item)
        added_count += 1

    # Clear the entire cart
    CartItem.query.delete()
    db.session.commit()

    return jsonify({
        "message": f"Purchase successful! {added_count} item(s) moved to your Pantry.",
        "items_added": added_count
    }), 200

# --- HOMEPAGE SPECIFIC ---

@app.route('/api/home_data', methods=['GET'])
def get_home_data():
    category = request.args.get('category', 'All')
    all_pantry = PantryItem.query.all()
    pantry_summary = {
        "total_items": len(all_pantry),
        "total_value": sum([i.price for i in all_pantry if i.price is not None]) or 0.0
    }
    
    def map_items(query_result):
        needs_commit = False
        resp = []
        for i in query_result:
            if not i.image_url:
                i.image_url = agents.get_image_url(i.name, i.category)
                needs_commit = True
            resp.append(i.to_dict())
        if needs_commit:
            db.session.commit()
        return resp
        
    if category and category != 'All':
        base_query = PantryItem.query.filter(PantryItem.category.ilike(f'%{category}%'))
        cat_items = map_items(base_query.all())
        return jsonify({
            "pantry_summary": pantry_summary,
            "is_category": True,
            "category_items": cat_items
        })
        
    popular = map_items(PantryItem.query.limit(4).all())
    recommended = map_items(PantryItem.query.order_by(PantryItem.id.desc()).limit(4).all())
    fresh = map_items(PantryItem.query.filter_by(category="Fresh").limit(4).all())
    dairy = map_items(PantryItem.query.filter_by(category="Dairy").limit(4).all())
    quick = map_items(PantryItem.query.filter(PantryItem.category.in_(["Frozen", "Snacks", "Grocery"])).limit(4).all())

    return jsonify({
        "pantry_summary": pantry_summary,
        "is_category": False,
        "popular": popular,
        "recommended": recommended,
        "fresh": fresh,
        "dairy": dairy,
        "quick": quick
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
