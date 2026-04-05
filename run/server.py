import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config.get("APP_HOST", "0.0.0.0"),
        port=app.config.get("APP_PORT", int(os.getenv("PORT", "5001"))),
        debug=app.config.get("DEBUG", False),
    )
