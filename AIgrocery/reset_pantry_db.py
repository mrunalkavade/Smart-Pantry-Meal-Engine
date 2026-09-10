import os
from app import app
from models import db

def reset_db():
    db_path = os.path.join('instance', 'pantry.db')
    if os.path.exists(db_path):
        print(f"Removing {db_path}...")
        os.remove(db_path)
    else:
        print(f"{db_path} not found.")
    
    with app.app_context():
        print("Creating all tables from current models...")
        db.create_all()
        print("Recreation successful.")

if __name__ == "__main__":
    reset_db()
