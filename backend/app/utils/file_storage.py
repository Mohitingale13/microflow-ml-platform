import json
import shutil
from pathlib import Path

from app.core.config import settings


def get_dataset_dir(dataset_id: str) -> Path:
    return Path(settings.STORAGE_BASE_PATH) / "datasets" / dataset_id


def get_raw_csv_path(dataset_id: str) -> Path:
    return get_dataset_dir(dataset_id) / "raw.csv"


def get_metadata_json_path(dataset_id: str) -> Path:
    return get_dataset_dir(dataset_id) / "metadata.json"


def save_raw_csv(dataset_id: str, content: bytes) -> str:
    dataset_dir = get_dataset_dir(dataset_id)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    csv_path = dataset_dir / "raw.csv"
    csv_path.write_bytes(content)
    return str(csv_path)


def save_metadata_json(dataset_id: str, metadata: dict) -> None:
    metadata_path = get_metadata_json_path(dataset_id)
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")


def delete_dataset_files(dataset_id: str) -> None:
    dataset_dir = get_dataset_dir(dataset_id)
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
