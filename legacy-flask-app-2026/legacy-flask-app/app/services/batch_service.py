import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from app.models import Activity, Application, Branch, Contact, Loan
from app.utils.serialization import model_to_dict


ENTITY_MAP = {
    "contacts": Contact,
    "loans": Loan,
    "applications": Application,
    "activities": Activity,
    "branches": Branch,
}


def export_entities(export_dir: str, export_format: str = "json") -> list[str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = Path(export_dir)
    target.mkdir(parents=True, exist_ok=True)

    output_paths = []
    for entity_name, model in ENTITY_MAP.items():
        rows = [model_to_dict(item) for item in model.query.all()]
        file_path = target / f"{entity_name}_{timestamp}.{export_format}"
        if export_format == "json":
            with file_path.open("w", encoding="utf-8") as handle:
                json.dump(rows, handle, indent=2)
        elif export_format == "csv":
            _write_csv(file_path, rows)
        else:
            raise ValueError("Unsupported export format. Use json or csv.")
        output_paths.append(str(file_path))

    return output_paths


def _write_csv(file_path: Path, rows: list[dict]):
    if not rows:
        with file_path.open("w", encoding="utf-8") as handle:
            handle.write("")
        return

    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
