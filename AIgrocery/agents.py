import os
import random
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai

# Load API keys
load_dotenv()
try:
    genai.configure(api_key=os.environ.get("API_KEY_AI_LLM", ""))
except Exception:
    pass

SPOONACULAR_KEY = os.environ.get("API_KEY_SPOONACULAR", "")
PEXELS_KEY = os.environ.get("API_KEY_PEXELS", "")
UNSPLASH_KEY = os.environ.get("API_KEY_UNSPLASH", "")

# Global in-memory cache for the session
IMAGE_CACHE = {}

# Natural Grocery Style V10 - Extended block list
INVALID_KEYWORDS = [
    # Cooked food / preparation
    'dish', 'cooked', 'recipe', 'meal', 'curry', 'fry', 'roasted', 'baked',
    'plate', 'bowl', 'serving', 'restaurant', 'garnish', 'plated', 'breakfast',
    'sambar', 'chutney', 'thali', 'chaat', 'tadka', 'tempering', 'gravy',
    'street food', 'appetizer', 'preparation', 'cuisine', 'delicious', 'vibrant',
    # Store / shelf
    'shelf', 'aisle', 'store', 'supermarket', 'shop'
]

def is_image_valid(metadata_text, specificity_level=0, is_recipe=False):
    """
    Validates if an image metadata suggests a raw product vs a cooked dish or store interior.
    If is_recipe is True, we ALLOW cooked/plating markers.
    """
    if not metadata_text:
        return specificity_level >= 2 
    
    text = metadata_text.lower()
    
    # Strictly reject shelves/stores for everyone
    for word in ['shelf', 'aisle', 'store', 'supermarket', 'shop', 'market']:
        if word in text:
            return False
            
    # For ingredients/products, reject cooked marker terms
    if not is_recipe:
        for word in INVALID_KEYWORDS:
            if word in text:
                return False
                
    return True

def get_image_url(query, category=None):
    if not query: return "https://loremflickr.com/320/240/grocery"
    
    clean_query = query.strip().lower()
    cat_lower = (category or "").lower()
    
    # v11 precision: context-aware grocery look
    cache_key = f"v11_precision_{clean_query}_{cat_lower}"
    
    if cache_key in IMAGE_CACHE:
        return IMAGE_CACHE[cache_key]

    # --- CATEGORY DETECTION ---
    is_recipe = any(k in cat_lower for k in ["recipe", "dish", "cook", "meal"]) or any(k in clean_query for k in ["pasta", "chicken", "salad", "soup", "curry"])
    indian_keywords = ["paneer", "ghee", "dal", "atta", "rice", "curd", "bhaji", "masala", "chai", "poha", "upma", "dhaniya", "jeera", "rai", "samosa", "biryani", "tikka", "roti", "paratha", "chole", "dahi", "turmeric", "haldi", "moong", "toor", "basmati"]
    is_indian = any(k in clean_query for k in indian_keywords)
    is_veg = any(k in clean_query for k in ["tomato", "onion", "potato", "carrot", "broccoli", "capsicum", "apple", "banana", "spinach", "chilli", "garlic", "ginger"])
    is_bread = any(k in clean_query for k in ["bread", "pav", "bun", "loaf"])

    # List of (Query, SpecificityLevel)
    search_attempts = []
    
    if is_recipe:
        search_attempts.append((f"{clean_query} dish plating", 2))
        search_attempts.append((f"{clean_query} food", 1))
    elif is_veg:
        search_attempts.append((f"{clean_query}vegetables", 2))
    elif is_indian:
        search_attempts.append((f"{clean_query} grocery packet", 2))
    elif is_bread:
        search_attempts.append((f"{clean_query} packet product", 2))
    else:
        # Default packaged logic
        search_attempts.append((f"{clean_query} packet product", 2))
        search_attempts.append((f"{clean_query} grocery", 1))

    # 2. Try APIs with Multi-Result Validation (checking up to 5)
    best_fallback_url = None

    for attempt_query, specificity in search_attempts:
        # Avoid keywords that cause dishes to appear for ingredients
        if not is_recipe:
            for bad in ["dish", "meal", "cooked", "recipe"]:
                attempt_query = attempt_query.replace(bad, "")

        # --- Try Unsplash ---
        if UNSPLASH_KEY:
            try:
                url = f"https://api.unsplash.com/search/photos?query={attempt_query}&per_page=5&client_id={UNSPLASH_KEY}"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    results = res.json().get("results", [])
                    for r in results:
                        meta = (r.get("alt_description") or "") + " " + (r.get("text") or "") # checking available descriptors
                        if is_image_valid(meta, specificity, is_recipe):
                            img_url = r["urls"]["small"]
                            IMAGE_CACHE[cache_key] = img_url
                            return img_url
                        if not best_fallback_url: best_fallback_url = r["urls"]["small"]
            except Exception: pass

        # --- Try Pexels ---
        if PEXELS_KEY:
            try:
                headers = {"Authorization": PEXELS_KEY}
                params = {"query": attempt_query, "per_page": 5}
                res = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=5)
                if res.status_code == 200:
                    photos = res.json().get("photos", [])
                    for p in photos:
                        meta = p.get("alt") or ""
                        if is_image_valid(meta, specificity, is_recipe):
                            img_url = p["src"]["medium"]
                            IMAGE_CACHE[cache_key] = img_url
                            return img_url
                        if not best_fallback_url: best_fallback_url = p["src"]["medium"]
            except Exception: pass

    # 3. Last Resort: Robust Fallback with precise tags (User Requirement #6)
    mock_url = f"https://loremflickr.com/320/240/{clean_query.replace(' ', ',')},grocery"
    IMAGE_CACHE[cache_key] = mock_url
    return mock_url

def get_nutrition(item_name):
    # Try Spoonacular
    if SPOONACULAR_KEY:
        try:
            params = {"apiKey": SPOONACULAR_KEY, "query": item_name}
            res = requests.get("https://api.spoonacular.com/recipes/guessNutrition", params=params, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if 'calories' in data:
                    return {"calories": data["calories"]["value"], "protein": f'{data["protein"]["value"]}g', "carbs": f'{data["carbs"]["value"]}g', "fat": f'{data["fat"]["value"]}g'}
        except Exception:
            pass
            
    # Fallback Local Heuristics
    protein = random.randint(1, 20)
    carbs = random.randint(5, 40)
    fat = random.randint(1, 15)
    return {"calories": (protein*4 + carbs*4 + fat*9), "protein": f"{protein}g", "carbs": f"{carbs}g", "fat": f"{fat}g"}

def simulate_receipt_parsing(receipt_text):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Extract grocery items from this text: '{receipt_text}'
        Return ONLY a JSON list of objects with this exact structure:
        [
            {{"name": "Item Name", "quantity": count (integer), "expiry_days": max_days_until_expiry (int), "category": "Fresh" | "Frozen" | "Dairy" | "Snacks" | "Pantry"}}
        ]
        Make logical guesses for expiry_days and category based on grocery type.
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        items = json.loads(text.strip())
        for item in items:
            item["image_url"] = get_image_url(item["name"])
        return items
    except Exception as e:
        print(f"Receipt parsing fallback -> {e}")
        return [
            {"name": "Chicken Breast", "quantity": 1, "expiry_days": 4, "category": "Fresh", "image_url": get_image_url("chicken")},
            {"name": "Whole Milk", "quantity": 2, "expiry_days": 7, "category": "Dairy", "image_url": get_image_url("milk")},
            {"name": "Baby Spinach", "quantity": 1, "expiry_days": 3, "category": "Fresh", "image_url": get_image_url("spinach")}
        ]

def get_healthier_alternative(item_name):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"Suggest exactly one healthier grocery alternative for: '{item_name}'. Reply with ONLY the name, no extra text.")
        alt = response.text.strip().strip('"')
        if alt: return alt
    except Exception:
        pass
    
    # Local fallback
    alternatives = { "olive oil": "Avocado Oil", "sugar": "Stevia", "white bread": "Whole Wheat Bread", "mayonnaise": "Greek Yogurt", "milk chocolate": "70% Dark Chocolate", "rice": "Quinoa" }
    for key, alt in alternatives.items():
        if key in item_name.lower(): return alt
    return f"Organic {item_name}"



def get_fallback_recipe(context_type, available_names, requested_dish=None):
    recipe_library = [
        {
            "title": "Pav Bhaji",
            "description": "Mashy vegetable curry served with buttered pav.",
            "raw_ingredients": ["Potatoes", "Cauliflower", "Peas", "Carrots", "Pav Bread", "Butter", "Pav Bhaji Masala"],
            "steps": ["Boil and mash vegetables.", "Sauté onions and spices in butter.", "Mix mashed vegetables and simmer.", "Serve with toasted pav."],
            "nutrition_tag": "Balanced", "macros": "12g Protein | 45g Carbs | 15g Fat"
        },
        {
            "title": "Paneer Butter Masala",
            "description": "Rich and creamy tomato-based paneer curry.",
            "raw_ingredients": ["Paneer", "Tomato Puree", "Cream", "Butter", "Ginger Garlic Paste", "Garam Masala"],
            "steps": ["Sauté ginger garlic paste.", "Add tomato puree and spices.", "Add paneer cubes and cream.", "Simmer for 5 minutes."],
            "nutrition_tag": "High Protein", "macros": "25g Protein | 15g Carbs | 30g Fat"
        },
        {
            "title": "Dal Tadka",
            "description": "Classic yellow lentils with a smoky tempering.",
            "raw_ingredients": ["Toor Dal", "Turmeric", "Cumin Seeds", "Garlic", "Dried Red Chilli", "Ghee"],
            "steps": ["Pressure cook lentils with turmeric.", "Prepare tadka with ghee, cumin, garlic, and chilli.", "Pour tadka over dal.", "Garnish with coriander."],
            "nutrition_tag": "High Protein", "macros": "18g Protein | 35g Carbs | 10g Fat"
        },
        {
            "title": "Veg Fried Rice",
            "description": "Quick and flavorful stir-fried rice with vegetables.",
            "raw_ingredients": ["Basmati Rice", "Carrots", "Beans", "Spring Onions", "Soy Sauce", "Ginger"],
            "steps": ["Cook rice and cool.", "Stir fry vegetables with ginger.", "Add rice and soy sauce.", "Toss on high heat."],
            "nutrition_tag": "Balanced", "macros": "8g Protein | 55g Carbs | 12g Fat"
        },
        {
            "title": "Pasta Alfredo",
            "description": "Creamy white sauce pasta with garlic and cheese.",
            "raw_ingredients": ["Pasta", "Heavy Cream", "Butter", "Parmesan Cheese", "Garlic"],
            "steps": ["Boil pasta.", "Melt butter with garlic and cream.", "Stir in cheese until smooth.", "Toss pasta in sauce."],
            "nutrition_tag": "High Calorie", "macros": "15g Protein | 60g Carbs | 35g Fat"
        },
        {
            "title": "Aloo Paratha",
            "description": "Whole wheat flatbread stuffed with spiced potatoes.",
            "raw_ingredients": ["Atta", "Potatoes", "Green Chilli", "Garam Masala", "Ghee"],
            "steps": ["Make dough and potato stuffing.", "Stuff dough with potatoes and roll.", "Cook on tawa with ghee.", "Serve hot with curd."],
            "nutrition_tag": "Balanced", "macros": "10g Protein | 50g Carbs | 15g Fat"
        },
        {
            "title": "Chole Masala",
            "description": "Spicy chickpea curry popular in North India.",
            "raw_ingredients": ["Chickpeas", "Onions", "Tomato", "Chole Masala", "Ginger", "Curd"],
            "steps": ["Soak and boil chickpeas.", "Make onion-tomato gravy.", "Add chickpeas and spices.", "Simmer until thickened."],
            "nutrition_tag": "High Protein", "macros": "20g Protein | 45g Carbs | 12g Fat"
        },
        {
            "title": "Grilled Chicken",
            "description": "Juicy grilled chicken breast with herbs.",
            "raw_ingredients": ["Chicken Breast", "Olive Oil", "Garlic", "Lemon Juice", "Black Pepper"],
            "steps": ["Marinate chicken with oil, garlic, and lemon.", "Preheat grill.", "Grill for 6-8 mins each side.", "Rest and serve."],
            "nutrition_tag": "High Protein", "macros": "45g Protein | 2g Carbs | 10g Fat"
        }
    ]
    
    # 1. PRIORITY: IF THE USER REQUESTED A SPECIFIC DISH, WE MUST SHOW IT.
    if requested_dish and requested_dish.lower() != "auto":
        req_lower = requested_dish.lower()
        # Search library
        for r in recipe_library:
            if req_lower in r["title"].lower():
                # Process and return this specific recipe
                return process_single_recipe(r, available_names)
        
        # If not in library, generate a dynamic on-the-fly recipe for THIS dish
        dynamic_r = {
            "title": requested_dish.title(),
            "description": f"A simple, delicious home-style {requested_dish}.",
            "raw_ingredients": [f"{requested_dish.title()} base", "Salt & Spices", "Oil/Butter", "Fresh Garnish"],
            "steps": [f"Prepare the main components for {requested_dish}.", "Sauté with aromatic spices and seasoning.", f"Cook until the {requested_dish} is perfectly tender.", "Garnish with fresh herbs and serve hot."],
            "nutrition_tag": "Balanced", "macros": "15g Protein | 35g Carbs | 12g Fat"
        }
        return process_single_recipe(dynamic_r, available_names)

    # 2. DEFAULT FALLBACK BEHAVIOR (e.g., "Suggest a meal")
    scored_recipes = [process_single_recipe(r, available_names) for r in recipe_library]
    scored_recipes.sort(key=lambda x: x["score"], reverse=True)
    
    if context_type == 'cart_recipes':
        return scored_recipes[:3]
    
    return scored_recipes[0]

def process_single_recipe(r, available_names):
    # Calculate status and scores for a specific recipe object
    r["ingredients_status"] = []
    r["missing_ingredients"] = []
    matches = 0
    for ing in r["raw_ingredients"]:
        if any(ing.lower() in avail.lower() for avail in available_names):
            r["ingredients_status"].append(f"✓ {ing}")
            matches += 1
        else:
            r["ingredients_status"].append(f"✗ {ing}")
            r["missing_ingredients"].append(ing)
    
    r["pantry_match_pct"] = int((matches / max(len(r["raw_ingredients"]), 1)) * 100)
    r["score"] = r["pantry_match_pct"]
    r["ingredients"] = r["ingredients_status"]
    r["image_url"] = get_image_url(r["title"], "recipe")
    return r

def generate_optimized_cart(needed_items):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        items_str = ", ".join(needed_items)
        prompt = f"""
        For these grocery items: {items_str}
        Provide realistic Indian Rupee (INR) prices for three stores: Instamart, BigBasket, and DMart.
        Also provide a standard measurement (e.g. "1 kg", "500g", "1 L").
        Sometimes provide a healthier or cheaper alternative name, otherwise keep the original name.
        
        Return exactly a JSON list of objects:
        [
            {{
                "original_name": "...",
                "name": "...",
                "measurement": "...",
                "badge": "Healthier Option" or "Cheapest Found",
                "description": "...",
                "category": "Grocery",
                "prices": {{
                    "Instamart": 250.0,
                    "BigBasket": 240.0,
                    "DMart": 260.0
                }}
            }}
        ]
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        data = json.loads(text.strip())
        
        optimized_cart = []
        for item in data:
            prices = item.get("prices", {})
            if not prices: prices = {"Instamart": 100.0, "BigBasket": 100.0, "DMart": 100.0}
            best_store = min(prices, key=prices.get)
            
            optimized_cart.append({
                "name": item.get("name", item.get("original_name", "")),
                "measurement": item.get("measurement", "1 Pack"),
                "prices": prices,
                "store": best_store,
                "price": prices[best_store],
                "badge": item.get("badge", "Cheapest Found"),
                "description": item.get("description", ""),
                "category": item.get("category", "Grocery"),
                "image_url": get_image_url(item.get("name", "food"))
            })
        return optimized_cart
    except Exception as e:
        print(f"Agent fallback mapping due to: {e}")
        stores = ["Instamart", "BigBasket", "DMart"]
        optimized_cart = []
        for item_name in needed_items:
            base_price = random.uniform(50.0, 300.0)
            prices = {
                "Instamart": round(base_price * random.uniform(0.9, 1.1), 2),
                "BigBasket": round(base_price * random.uniform(0.9, 1.1), 2),
                "DMart": round(base_price * random.uniform(0.8, 1.0), 2)
            }
            best_store = min(prices, key=prices.get)
            optimized_cart.append({
                "name": item_name,
                "measurement": "1 Pack",
                "prices": prices,
                "store": best_store, 
                "price": prices[best_store],
                "badge": "Cheapest Found",
                "description": "Fallback auto-generated pricing.",
                "image_url": get_image_url(item_name),
                "category": "Grocery"
            })
        return optimized_cart

# In-memory cache for the session
CHAT_CACHE = {}

def chatbot_response(query, pantry_items):
    query_clean = query.strip().lower()
    
    # 1. Check Cache
    if query_clean in CHAT_CACHE:
        return CHAT_CACHE[query_clean]
    
    pantry_str = ", ".join([f"{p.name}" for p in pantry_items])
    
    # 2. Local Intent Detection (Selective API Usage)
    # --- RECIPE DETECTION (USER SPECIFIED LOGIC) ---
    recipe_keywords = ["recipe for", "how to make", "make"]
    for keyword in recipe_keywords:
        if keyword in query_clean:
            dish = query_clean.split(keyword)[-1].strip()
            if not dish: dish = "healthy meal"
            response = f"RENDER_RECIPE_CARD_MANUAL:{dish}"
            CHAT_CACHE[query_clean] = response
            return response

    # Simple Cart Addition
    if any(word in query_clean for word in ["add", "buy", "get"]) and any(word in query_clean for word in ["cart", "grocery", "list"]):
        items = query_clean.replace("add", "").replace("to cart", "").replace("to my cart", "").replace("buy", "").strip()
        if items:
            response = f"ADD_TO_CART_TRIGGERED:{items}"
            CHAT_CACHE[query_clean] = response
            return response

    # Simple Pantry Check
    if any(word in query_clean for word in ["pantry", "have", "stock", "items"]):
        if not pantry_items:
            return "Your pantry is currently empty! Would you like to scan a receipt or add some essentials?"
        return f"You currently have {len(pantry_items)} items in your pantry, including {pantry_str[:100]}... What would you like to cook with them?"

    # 3. Hybrid API Fallback / Complex Intent
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        You are a Dedicated Smart Grocery Assistant. 
        User Query: '{query}'
        User Pantry: {pantry_str}

        EXTRACT INTENT:
        - Recipe Request: Detect if the user wants a recipe.
        - Pantry-based Meal: "what can I cook", "suggest meals"
        - Grocery/Cart: "add [item]", "suggest what to buy"
        - General Help: "how can you help"

        STRICT RESPONSE RULES:
        1. If Recipe Request: Extract the EXACT dish name (X) from phrases like "recipe for X", "how to make X", or "make X". 
           - Return EXACTLY 'RENDER_RECIPE_CARD_MANUAL:X'.
           - If no dish is specified, use 'healthy meal'.
           - Do NOT invent or default to other dishes.
        2. If Pantry Meal Suggestion: Return EXACTLY 'RENDER_RECIPE_PANTRY'.
        3. If Grocery/Cart Add: Return EXACTLY 'ADD_TO_CART_TRIGGERED:<item1,item2>'.
        4. For everything else, be a helpful, concise Grocery Assistant.
        
        DO NOT include unrelated conversational filler. Be direct.
        """
        res = model.generate_content(prompt)
        text = res.text.strip()
        
        # Cache and return
        CHAT_CACHE[query_clean] = text
        return text

    except Exception as e:
        print(f"Chatbot API fail (using robust fallback): {e}")
        # 4. Robust Local Fallback
        if any(p in query_clean for p in ["recipe", "make", "how to"]):
            parts = []
            if "recipe for" in query_clean: parts = query_clean.split("recipe for")
            elif "how to make" in query_clean: parts = query_clean.split("how to make")
            elif "make" in query_clean: parts = query_clean.split("make")
            
            dish = parts[-1].strip() if len(parts) > 1 else "healthy meal"
            return f"RENDER_RECIPE_CARD_MANUAL:{dish}"
        
        if any(word in query_clean for word in ["cook", "meal", "dinner", "lunch", "pantry"]):
            return "RENDER_RECIPE_PANTRY"
            
        return "I'm here to help! I can suggest recipes based on your pantry or help you optimize your grocery cart."

def generate_recipe(context_type, query, available_items, cart_items=None):
    available_names = [i.name.lower() for i in available_items]
    if cart_items:
        available_names.extend([i.name.lower() for i in cart_items])
        
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        pantry_str = ", ".join(available_names)
        
        prompt = f"""
        Create a recipe for: {query}.
        Available items: {pantry_str}.
        
        Rules:
        - Prioritize available items.
        - Mark ingredients: ✓ [Item] (if available) or ✗ [Item] (if missing).
        - Provide dish name, description, ingredients list, and 4-6 clear steps.
        
        Return JSON:
        {{
            "recipes": [
                {{
                    "title": "...",
                    "description": "...",
                    "raw_ingredients": ["..."],
                    "steps": ["..."],
                    "nutrition_tag": "...",
                    "macros": "..."
                }}
            ]
        }}
        """
        if context_type == 'cart_recipes':
            prompt += " Generate 3 recipes."
        else:
            prompt += " Generate 1 recipe."

        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        
        data = json.loads(text.strip())
        recipes = data.get("recipes", [])
        
        for r in recipes:
            r["image_url"] = get_image_url(r["title"], "recipe")
            r["ingredients_status"] = []
            r["missing_ingredients"] = []
            matches = 0
            for ing in r["raw_ingredients"]:
                # Better matching logic
                if any(word in [avail.split()[0].lower() for avail in available_names] for word in ing.lower().split() if len(word) > 3):
                    r["ingredients_status"].append(f"✓ {ing}")
                    matches += 1
                elif any(avail in ing.lower() for avail in available_names):
                    r["ingredients_status"].append(f"✓ {ing}")
                    matches += 1
                else:
                    r["ingredients_status"].append(f"✗ {ing}")
                    r["missing_ingredients"].append(ing)
            
            r["pantry_match_pct"] = int((matches / max(len(r["raw_ingredients"]), 1)) * 100)
            r["score"] = r["pantry_match_pct"]
            r["ingredients"] = r["ingredients_status"]
            
        recipes.sort(key=lambda x: x["score"], reverse=True)
        if context_type == 'cart_recipes': return recipes
        return recipes[0] if recipes else get_fallback_recipe(context_type, available_names, query)

    except Exception as e:
        print(f"Gemini recipe fail: {e}")
        return get_fallback_recipe(context_type, available_names, query)
