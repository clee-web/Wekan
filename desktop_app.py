import os
import sys
import threading
import time
import signal
import atexit
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the Flask app
from app import app, db

import webview

class Api:
    """Optional: Expose Python APIs to the webview window if needed."""
    def __init__(self):
        pass

def run_flask():
    """Run Flask app with waitress in background thread."""
    from waitress import serve
    print("Starting Flask server on http://127.0.0.1:8000...")
    serve(app, host='127.0.0.1', port=8000, threads=4)

def shutdown_servers():
    """Graceful shutdown."""
    print("Shutting down...")

def main():
    # Ensure database directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Create app context and ensure tables exist
    with app.app_context():
        db.create_all()
    
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait a moment for server to start
    time.sleep(2)
    
    # Create pywebview window
    window = webview.create_window(
        'Academy Management System',
        'http://127.0.0.1:8000/',
        width=1400,
        height=900,
        min_size=(1200, 800),
        resizable=True,
        on_top=False,
        easy_drag=True,
        # No dev tools for production
        # devtools=False,
    )
    
    def on_closed():
        shutdown_servers()
    
    window.events.closed += on_closed
    
    # Run webview
    webview.start(debug=False, http_server=False)

if __name__ == '__main__':
    # Handle graceful shutdown
    atexit.register(shutdown_servers)
    
    try:
        main()
    except KeyboardInterrupt:
        shutdown_servers()

