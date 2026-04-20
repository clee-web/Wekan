import os
import sys
import threading
import time
import subprocess
import webview
from pathlib import Path

# Directory of this script
BASE_DIR = Path(__file__).parent

def run_flask_background():
    """Run your existing app.py on port 8000."""
    # Change to project dir
    os.chdir(BASE_DIR)
    # Run app.py with waitress (or default port 5000)
    cmd = [sys.executable, 'app.py']
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Flask started (PID {proc.pid}) on http://127.0.0.1:5000")
    return proc

def main():
    flask_proc = run_flask_background()
    
    # Wait for server start
    time.sleep(3)
    
    # Open webview
    window = webview.create_window(
        'Academy Management',
        'http://127.0.0.1:5000/',
        width=1400,
        height=900,
        min_size=(1200, 800),
    )
    
    def on_closed():
        flask_proc.terminate()
        flask_proc.wait()
    
    window.events.closed += on_closed
    
    webview.start()

if __name__ == '__main__':
    main()

