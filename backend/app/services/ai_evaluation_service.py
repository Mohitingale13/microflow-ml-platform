"""
ai_evaluation_service.py — Batch evaluator for AIQueryCache using RAGAS-style metrics.

Uses Gemini as a Judge to score:
1. Context Relevance
2. Faithfulness
3. Answer Relevance
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from sqlalchemy.orm import Session
from app.repositories.ai_query_repository import AIQueryRepository

if TYPE_CHECKING:
    from app.ai.gemini_service import GeminiService

logger = logging.getLogger(__name__)

MAX_EVALUATION_ATTEMPTS: int = 3

EVALUATION_PROMPT = """
You are an expert AI evaluator grading a Retrieval-Augmented Generation (RAG) system.
Given the User's Question, the Retrieved Context, and the AI's Answer, you must evaluate the response across 3 metrics (scores 0.0 to 1.0).

Question:
{question}

Retrieved Context:
{context}

AI Answer:
{answer}

Evaluate these metrics strictly:
1. context_relevance_score: How relevant is the retrieved context to the user's question? (0.0 = completely irrelevant, 1.0 = highly relevant)
2. faithfulness_score: Is the answer entirely based on the provided context? (0.0 = hallucinated or external info used, 1.0 = strictly derived from context)
3. answer_relevance_score: How well does the answer address the user's question? (0.0 = completely ignores question, 1.0 = answers perfectly)

Provide a brief reasoning, then the scores.
Output STRICTLY in this JSON format:
{{
  "evaluation_reasoning": "string",
  "context_relevance_score": float,
  "faithfulness_score": float,
  "answer_relevance_score": float
}}
"""


class AIEvaluationService:
    def __init__(self, query_repo: AIQueryRepository, gemini_service: GeminiService):
        self._query_repo = query_repo
        self._gemini = gemini_service

    def evaluate_batch(self, db: Session, limit: int = 10) -> int:
        """
        Evaluate up to `limit` unevaluated AI queries and persist scores.
        Returns the number of queries successfully evaluated.
        """
        unevaluated = self._query_repo.get_unevaluated(limit=limit, db=db)
        if not unevaluated:
            return 0

        evaluated_count = 0
        has_updates = False

        for record in unevaluated:
            prompt = EVALUATION_PROMPT.format(
                question=record.question,
                context=record.supporting_data,
                answer=record.answer
            )

            try:
                response_text = self._gemini.generate_evaluation(prompt)
                
                # Strip json markdown if present
                clean_text = response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]

                result = json.loads(clean_text)

                record.context_relevance_score = float(result.get("context_relevance_score", 0.0))
                record.faithfulness_score = float(result.get("faithfulness_score", 0.0))
                record.answer_relevance_score = float(result.get("answer_relevance_score", 0.0))
                record.evaluation_reasoning = str(result.get("evaluation_reasoning", "No reasoning provided."))
                record.evaluation_status = "completed"
                record.evaluation_error = None
                
                db.add(record)
                evaluated_count += 1
                has_updates = True
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to evaluate query {record.id}: {error_msg}")
                record.evaluation_retries += 1
                record.evaluation_error = error_msg
                if record.evaluation_retries >= MAX_EVALUATION_ATTEMPTS:
                    record.evaluation_status = "failed"
                else:
                    record.evaluation_status = "pending"
                db.add(record)
                has_updates = True
        
        # Commit the batch if any records were updated (evaluated or retried/failed)
        if has_updates:
            db.commit()

        return evaluated_count
