"""Launch KidSpark with: python -m streamlit run app.py."""
from pathlib import Path
import sys

# Find this checkout's package even without an editable installation.
source_directory = str(Path(__file__).resolve().parent / 'src')
if source_directory not in sys.path:
    sys.path.insert(0, source_directory)

from kidspark.ui.app import main

main()
