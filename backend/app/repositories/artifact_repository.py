"""
artifact_repository.py — Data access for Artifact records.
"""

from sqlalchemy.orm import Session

from app.models.artifact import Artifact, ArtifactType


class ArtifactRepository:
    def create(
        self,
        db: Session,
        *,
        run_id: str,
        experiment_id: str,
        dataset_id: str,
        artifact_type: ArtifactType,
        filename: str,
        mime_type: str,
        storage_path: str,
        file_size_bytes: int,
        sha256_checksum: str,
    ) -> Artifact:
        artifact = Artifact(
            run_id=run_id,
            experiment_id=experiment_id,
            dataset_id=dataset_id,
            artifact_type=artifact_type,
            filename=filename,
            mime_type=mime_type,
            storage_path=storage_path,
            file_size_bytes=file_size_bytes,
            sha256_checksum=sha256_checksum,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact

    def get_by_id(self, artifact_id: str, db: Session) -> Artifact | None:
        return db.query(Artifact).filter(Artifact.id == artifact_id).first()

    def list_all(self, db: Session) -> list[Artifact]:
        return db.query(Artifact).order_by(Artifact.created_at.desc()).all()

    def list_by_run(self, run_id: str, db: Session) -> list[Artifact]:
        return (
            db.query(Artifact)
            .filter(Artifact.run_id == run_id)
            .order_by(Artifact.artifact_type)
            .all()
        )

    def list_by_experiment(self, experiment_id: str, db: Session) -> list[Artifact]:
        return (
            db.query(Artifact)
            .filter(Artifact.experiment_id == experiment_id)
            .order_by(Artifact.created_at.desc())
            .all()
        )

    def delete_by_run(self, run_id: str, db: Session) -> None:
        db.query(Artifact).filter(Artifact.run_id == run_id).delete()
        db.commit()

    def count_by_type(self, artifact_type: ArtifactType, db: Session) -> int:
        from sqlalchemy import func
        return db.query(func.count(Artifact.id)).filter(
            Artifact.artifact_type == artifact_type
        ).scalar() or 0

    def total_size_bytes(self, db: Session) -> int:
        from sqlalchemy import func
        return db.query(func.sum(Artifact.file_size_bytes)).scalar() or 0
