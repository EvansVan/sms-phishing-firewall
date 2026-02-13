"""
Seed database with sample data (for testing).
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import Subscriber

app = create_app()

with app.app_context():
    # Add sample subscribers
    sample_subscribers = [
        {'phone_number': '+254712345678', 'region': 'Nairobi'},
        {'phone_number': '+254723456789', 'region': 'Mombasa'},
        {'phone_number': '+254734567890', 'region': 'Kisumu'},
    ]

    for sub_data in sample_subscribers:
        existing = Subscriber.query.filter_by(phone_number=sub_data['phone_number']).first()
        if not existing:
            subscriber = Subscriber(**sub_data)
            db.session.add(subscriber)
            print(f"Added subscriber: {sub_data['phone_number']}")

    db.session.commit()
    print("Sample data seeded successfully!")

