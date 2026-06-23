import os
import runpy
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(ROOT, "laptop_project")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

if __name__ == "__main__":
    runpy.run_path(os.path.join(PROJECT_DIR, "main.py"), run_name="__main__")
