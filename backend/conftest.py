import sys
from pathlib import Path

# Add the project root (parent of backend/) to sys.path so `import backend.*` resolves.
sys.path.insert(0, str(Path(__file__).parent.parent))
