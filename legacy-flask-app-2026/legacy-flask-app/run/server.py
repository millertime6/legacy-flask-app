import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
