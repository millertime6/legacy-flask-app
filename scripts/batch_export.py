import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.services.batch_service import export_entities


def run_export(fmt: str):
    app = create_app()
    with app.app_context():
        output_files = export_entities(app.config["BATCH_EXPORT_DIR"], export_format=fmt)
        print("Export complete:")
        for path in output_files:
            print(f"- {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export daily batch extracts for downstream sync.")
    parser.add_argument(
        "--format",
        default="json",
        choices=["json", "csv"],
        help="Output format for exported entity snapshots.",
    )
    args = parser.parse_args()
    run_export(args.format)
