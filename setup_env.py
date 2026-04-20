import os
import subprocess
import sys

# Create virtual environment
subprocess.run([sys.executable, "-m", "venv", "venv"])

# Activate virtual environment
activate_script = os.path.join("venv", "Scripts", "activate")
subprocess.run([activate_script], shell=True)

# Install dependencies
subprocess.run(["pip", "install", "-r", "requirements.txt"])
