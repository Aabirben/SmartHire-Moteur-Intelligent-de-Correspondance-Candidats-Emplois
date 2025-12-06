import sys
from pathlib import Path

# Ligne miracle – à garder pour toujours
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Cela pour runner le serveur flask pour le backend 
from app import app

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')