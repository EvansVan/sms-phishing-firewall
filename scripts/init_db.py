"""
Initialize database and create tables.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env into the process (so app config picks up variables)
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database initialized successfully!")
    print("Tables created: ScamLog, Blacklist, Subscriber, Campaign")

