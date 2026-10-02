import sys
import os


path = sys.path[0] 

try:
    exec(open(f"{path}/main.py").read())
except Exception as e:
    print(f"Error: {e}")