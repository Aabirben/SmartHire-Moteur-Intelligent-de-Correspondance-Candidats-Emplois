import sys
from pathlib import Path

# Ligne miracle – à garder pour toujours
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))