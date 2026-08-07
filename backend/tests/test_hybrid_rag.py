"""
tests/test_hybrid_rag.py — Comprehensive unit and integration tests for Hybrid RAG functionality.

All embedding calls and Gemini model invocations are mocked to ensure tests run offline
without requiring active API keys or external network requests.
"""

from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.document_embedding import DocumentEmbedding
from app.repositories.document_embedding_repository import DocumentEmbeddingRepository
from app.services.embedding_service import EmbeddingService


@pytest.fixture(scope="module")
def db_engine():
    """Create in-memory SQLite engine for vector repository unit testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Provide clean database session per test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_document_embedding_repository_upsert(db_session):
    """Test upserting a DocumentEmbedding record."""
    repo = DocumentEmbeddingRepository()
    dummy_vector = [0.1] * 768

    rec1 = repo.upsert_embedding(
        db=db_session,
        document_type="run_ai_review",
        document_id="rev-1",
        content="Review content 1",
        embedding=dummy_vector,
        metadata_json={"title": "Test Review 1"},
    )
    assert rec1.id is not None
    assert rec1.document_type == "run_ai_review"
    assert rec1.document_id == "rev-1"
    assert rec1.content == "Review content 1"

    # Test update existing
    rec2 = repo.upsert_embedding(
        db=db_session,
        document_type="run_ai_review",
        document_id="rev-1",
        content="Updated content 1",
        embedding=dummy_vector,
        metadata_json={"title": "Updated Review 1"},
    )
    assert rec2.id == rec1.id
    assert rec2.content == "Updated content 1"


def test_embedding_service_indexing_with_mocked_gemini(db_session):
    """Test EmbeddingService indexing methods with mocked Gemini embeddings."""
    mock_gemini = MagicMock()
    mock_gemini.generate_embedding.return_value = [0.05] * 768

    service = EmbeddingService(gemini_service=mock_gemini)

    # Mock domain objects
    mock_review = MagicMock(id="rev-100", overall_assessment="Assessment", strengths="Good", weaknesses="None", comparison="N/A", recommendation="Next")
    mock_run = MagicMock(id="run-100", run_number=1, model_type="xgboost")
    mock_experiment = MagicMock(id="exp-100", name="XGBoost Test")

    service.index_ai_review(db_session, mock_review, mock_run, mock_experiment)

    repo = DocumentEmbeddingRepository()
    fetched = repo.get_by_type_and_id(db_session, "run_ai_review", "rev-100")
    assert fetched is not None
    assert "XGBoost Test" in fetched.content
    assert fetched.metadata_json["run_number"] == 1


def test_semantic_retrieval_service_flow(db_session):
    """Test retrieve_semantic_context returns formatted search results."""
    mock_gemini = MagicMock()
    mock_gemini.generate_embedding.return_value = [0.1] * 768

    repo = DocumentEmbeddingRepository()
    repo.upsert_embedding(
        db=db_session,
        document_type="experiment_ai_strategy",
        document_id="strat-1",
        content="Document Type: AI Experiment Strategy\nTitle: Strategy Title\nContent body snippet",
        embedding=[0.1] * 768,
        metadata_json={"title": "Strategy Title"},
    )

    service = EmbeddingService(gemini_service=mock_gemini, embedding_repo=repo)
    results = service.retrieve_semantic_context(db_session, query_text="What strategy should we use?", limit=5)

    assert len(results) >= 1
    first = results[0]
    assert first["document_type"] == "experiment_ai_strategy"
    assert first["title"] == "Strategy Title"
    assert "Content body snippet" in first["snippet"]
