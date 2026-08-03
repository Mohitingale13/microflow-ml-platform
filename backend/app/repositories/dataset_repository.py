from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetStatus


class DatasetRepository:
    def create(
        self,
        db: Session,
        *,
        name: str,
        description: str | None,
        original_filename: str,
        file_hash: str,
        file_size_bytes: int,
        storage_path: str,
    ) -> Dataset:
        dataset = Dataset(
            name=name,
            description=description,
            original_filename=original_filename,
            file_hash=file_hash,
            file_size_bytes=file_size_bytes,
            storage_path=storage_path,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    def get_by_id(self, dataset_id: str, db: Session) -> Dataset | None:
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()

    def get_by_hash(self, file_hash: str, db: Session) -> Dataset | None:
        return db.query(Dataset).filter(Dataset.file_hash == file_hash).first()

    def list_all(self, db: Session) -> list[Dataset]:
        return (
            db.query(Dataset).order_by(Dataset.created_at.desc()).all()
        )

    def update(self, db: Session, dataset: Dataset, **kwargs: Any) -> Dataset:
        for key, value in kwargs.items():
            setattr(dataset, key, value)
        dataset.updated_at = datetime.now(timezone.utc)
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    def delete(self, dataset_id: str, db: Session) -> None:
        dataset = self.get_by_id(dataset_id, db)
        if dataset:
            db.delete(dataset)
            db.commit()
