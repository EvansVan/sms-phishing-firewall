"""
Application entry point.
"""
import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env into the process
load_dotenv()

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

