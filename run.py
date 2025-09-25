import subprocess
import sys

command = [sys.executable,'-m', "streamlit", "run", "Login.py"]
process = subprocess.Popen(command)