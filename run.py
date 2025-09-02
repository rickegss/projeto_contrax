import subprocess
import sys

command = [sys.executable,'-m', "streamlit", "run", "home.py"]
process = subprocess.Popen(command)