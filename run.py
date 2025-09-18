import subprocess
import sys

command = [sys.executable,'-m', "streamlit", "run", "Home.py"]
process = subprocess.Popen(command)