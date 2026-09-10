import sqlite3
import os

db_path = 'instance/pantry.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables first
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables found: {tables}")
    
    if 'pantry_item' in tables:
        cursor.execute("UPDATE pantry_item SET image_url = NULL")
        print(f"Purged image_url from pantry_item.")
    
    if 'cart_item' in tables:
        cursor.execute("UPDATE cart_item SET image_url = NULL")
        print(f"Purged image_url from cart_item.")
        
    conn.commit()
    conn.close()
    print("Purge complete.")
