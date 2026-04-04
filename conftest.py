import sys
from pathlib import Path

# Add python/ to sys.path so that `src.*` imports work from tests/
sys.path.insert(0, str(Path(__file__).parent / "python"))
