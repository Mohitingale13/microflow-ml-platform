"""
services/embedding_service.py — High-level domain indexing and semantic retrieval service for Hybrid RAG.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from sqlalchemy.orm import Session

from app.ai.gemini_service import GeminiService
from app.repositories.document_embedding_repository import DocumentEmbeddingRepository

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service orchestrating document embedding generation, indexing, and pgvector semantic retrieval."""

    def __init__(
        self,
        gemini_service: GeminiService | None = None,
        embedding_repo: DocumentEmbeddingRepository | None = None,
    ) -> None:
        self._gemini = gemini_service or GeminiService()
        self._repo = embedding_repo or DocumentEmbeddingRepository()

    # ── Indexing Methods ────────────────────────────────────────────────────────

    def index_ai_review(self, db: Session, review_record: Any, run: Any, experiment: Any) -> None:
        """Format and index an AI Run Review as a searchable document embedding."""
        try:
            exp_name = experiment.name if experiment else "Unknown Experiment"
            run_num = run.run_number if run else "Unknown"
            model_type = run.model_type if run else "Model"

            title = f"AI Run Review — {exp_name} (Run #{run_num})"
            content = (
                f"Document Type: AI Run Review\n"
                f"Title: {title}\n"
                f"Model: {model_type}\n"
                f"Overall Assessment: {review_record.overall_assessment}\n"
                f"Strengths: {review_record.strengths}\n"
                f"Weaknesses: {review_record.weaknesses}\n"
                f"Comparison: {review_record.comparison}\n"
                f"Recommendation: {review_record.recommendation}"
            )

            metadata = {
                "title": title,
                "experiment_id": str(experiment.id) if experiment else None,
                "run_id": str(run.id) if run else None,
                "run_number": run_num,
                "model_type": model_type,
            }

            vector = self._gemini.generate_embedding(content)
            self._repo.upsert_embedding(
                db=db,
                document_type="run_ai_review",
                document_id=str(review_record.id),
                content=content,
                embedding=vector,
                metadata_json=metadata,
            )
        except Exception as exc:
            logger.error("Failed to index AI Review %s: %s", getattr(review_record, "id", "N/A"), exc)

    def index_ai_strategy(self, db: Session, strategy_record: Any, experiment: Any) -> None:
        """Format and index an AI Experiment Strategy as a searchable document embedding."""
        try:
            exp_name = experiment.name if experiment else "Unknown Experiment"
            data_map = {}
            if getattr(strategy_record, "strategy_json", None):
                try:
                    data_map = json.loads(strategy_record.strategy_json)
                except Exception:
                    pass

            title = f"AI Experiment Strategy — {exp_name}"
            content = (
                f"Document Type: AI Experiment Strategy\n"
                f"Title: {title}\n"
                f"Status: {data_map.get('current_experiment_status', 'Active')}\n"
                f"Overall Assessment: {data_map.get('overall_assessment', '')}\n"
                f"Strongest Model: {data_map.get('strongest_model', '')}\n"
                f"Learned Findings: {' '.join(data_map.get('what_has_been_learned', []))}\n"
                f"Recommended Next Steps: {json.dumps(data_map.get('recommended_next_experiment', {}))}\n"
                f"Risks: {' '.join(data_map.get('potential_risks', []))}"
            )

            metadata = {
                "title": title,
                "experiment_id": str(experiment.id) if experiment else None,
                "confidence": data_map.get("confidence", "Medium"),
            }

            vector = self._gemini.generate_embedding(content)
            self._repo.upsert_embedding(
                db=db,
                document_type="experiment_ai_strategy",
                document_id=str(strategy_record.id),
                content=content,
                embedding=vector,
                metadata_json=metadata,
            )
        except Exception as exc:
            logger.error("Failed to index AI Strategy %s: %s", getattr(strategy_record, "id", "N/A"), exc)

    def index_ai_comparison(self, db: Session, comparison_record: Any, run_a: Any, run_b: Any, experiment: Any) -> None:
        """Format and index an AI Run Comparison as a searchable document embedding."""
        try:
            exp_name = experiment.name if experiment else "Unknown Experiment"
            a_num = run_a.run_number if run_a else "A"
            b_num = run_b.run_number if run_b else "B"

            title = f"AI Run Comparison — {exp_name} (Run #{a_num} vs Run #{b_num})"
            content = (
                f"Document Type: AI Run Comparison\n"
                f"Title: {title}\n"
                f"Better Performing Model: {comparison_record.better_run}\n"
                f"Overall Summary: {comparison_record.overall_summary}\n"
                f"Key Improvements: {comparison_record.key_improvements}\n"
                f"Tradeoffs: {comparison_record.tradeoffs}\n"
                f"Configuration Analysis: {comparison_record.configuration_analysis}\n"
                f"Next Recommendation: {comparison_record.next_recommendation}"
            )

            metadata = {
                "title": title,
                "experiment_id": str(experiment.id) if experiment else None,
                "run_a_id": str(run_a.id) if run_a else None,
                "run_b_id": str(run_b.id) if run_b else None,
            }

            vector = self._gemini.generate_embedding(content)
            self._repo.upsert_embedding(
                db=db,
                document_type="run_ai_comparison",
                document_id=str(comparison_record.id),
                content=content,
                embedding=vector,
                metadata_json=metadata,
            )
        except Exception as exc:
            logger.error("Failed to index AI Comparison %s: %s", getattr(comparison_record, "id", "N/A"), exc)

    def index_dataset_analysis(self, db: Session, analysis_record: Any, dataset: Any) -> None:
        """Format and index a Dataset AI Intelligence analysis as a searchable document embedding."""
        try:
            ds_name = dataset.name if dataset else "Unknown Dataset"
            data_map = {}
            if getattr(analysis_record, "analysis_json", None):
                try:
                    data_map = json.loads(analysis_record.analysis_json)
                except Exception:
                    pass

            title = f"Dataset Intelligence — {ds_name}"
            content = (
                f"Document Type: Dataset Intelligence\n"
                f"Title: {title}\n"
                f"Summary: {data_map.get('overall_summary', '')}\n"
                f"Recommended Target Column: {data_map.get('recommended_target', '')}\n"
                f"Potential Data Issues: {' '.join(data_map.get('potential_issues', []))}\n"
                f"Recommended Models: {' '.join(data_map.get('recommended_models', []))}\n"
                f"Risk Assessment: {data_map.get('risk_assessment', '')}"
            )

            metadata = {
                "title": title,
                "dataset_id": str(dataset.id) if dataset else None,
                "dataset_name": ds_name,
            }

            vector = self._gemini.generate_embedding(content)
            self._repo.upsert_embedding(
                db=db,
                document_type="dataset_ai_analysis",
                document_id=str(analysis_record.id),
                content=content,
                embedding=vector,
                metadata_json=metadata,
            )
        except Exception as exc:
            logger.error("Failed to index Dataset Analysis %s: %s", getattr(analysis_record, "id", "N/A"), exc)

    def index_experiment_description(self, db: Session, experiment: Any) -> None:
        """Format and index an Experiment's objective and narrative description."""
        try:
            if not experiment or not (experiment.description or experiment.objective):
                return

            title = f"Experiment Objective — {experiment.name}"
            content = (
                f"Document Type: Experiment Description\n"
                f"Title: {title}\n"
                f"Experiment Name: {experiment.name}\n"
                f"Objective: {experiment.objective or 'Not specified'}\n"
                f"Description: {experiment.description or 'No description provided'}"
            )

            metadata = {
                "title": title,
                "experiment_id": str(experiment.id),
                "experiment_name": experiment.name,
            }

            vector = self._gemini.generate_embedding(content)
            self._repo.upsert_embedding(
                db=db,
                document_type="experiment_description",
                document_id=str(experiment.id),
                content=content,
                embedding=vector,
                metadata_json=metadata,
            )
        except Exception as exc:
            logger.error("Failed to index Experiment Description %s: %s", getattr(experiment, "id", "N/A"), exc)

    # ── Retrieval Method ────────────────────────────────────────────────────────

    def retrieve_semantic_context(
        self, db: Session, query_text: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Generate query vector for query_text and perform Top-K similarity search in pgvector.
        Returns list of structured document dictionaries for context building and source attribution.
        """
        if not query_text or not query_text.strip():
            return []

        try:
            query_vector = self._gemini.generate_embedding(query_text.strip())
            matches = self._repo.search_similar(db, query_vector=query_vector, limit=limit)

            retrieved = []
            for doc, distance in matches:
                meta = doc.metadata_json or {}
                title = meta.get("title", f"{doc.document_type} ({doc.document_id[:8]})")

                # Create a clean 200-char snippet for UI source preview
                lines = doc.content.split("\n")
                snippet_body = " ".join([l for l in lines if not l.startswith("Document Type:") and not l.startswith("Title:")])
                snippet = snippet_body[:220] + "..." if len(snippet_body) > 220 else snippet_body

                # Similarity score calculation (1 - distance for cosine)
                similarity_score = round(max(0.0, 1.0 - distance), 4)

                retrieved.append({
                    "document_type": doc.document_type,
                    "document_id": doc.document_id,
                    "title": title,
                    "content": doc.content,
                    "snippet": snippet,
                    "score": similarity_score,
                    "metadata": meta,
                })
            return retrieved
        except Exception as exc:
            logger.error("Semantic retrieval failed for query '%s': %s", query_text[:50], exc)
            return []
