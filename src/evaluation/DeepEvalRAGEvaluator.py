import json
import os
import logging
import math
from typing import List

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric
)
from deepeval.models import OllamaModel

from helpers.config import Settings

logger = logging.getLogger(__name__)
os.environ["DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE"] = "600"


class DeepEvalRAGEvaluator:

    def __init__(self, nlp_controller):
        self.results = []
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.evaluation_data_path = os.path.join(
            self.base_dir, "evaluation/evaluation_dataset.json"
        )
        self.test_questions = []
        self.nlp_controller = nlp_controller
        self.settings = Settings()

    # -----------------------------------------------------
    # Load JSON evaluation dataset
    # -----------------------------------------------------
    def load_evaluation_data(self):
        with open(self.evaluation_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.test_questions = data["Questions"]
        logger.info(f"Loaded {len(self.test_questions)} evaluation questions.")

    # -----------------------------------------------------
    # Model used for DeepEval metrics
    # -----------------------------------------------------
    def get_evaluation_model(self):
        return OllamaModel(
            model="phi3.5:3.8b",
            base_url="https://conjunctional-superrenal-maeve.ngrok-free.dev"
        )

    # -----------------------------------------------------
    # Create DeepEval metrics
    # -----------------------------------------------------
    def create_metrics(self, model, include_ground_truth_metrics=True):
        metrics = [
            AnswerRelevancyMetric(threshold=0.7, model=model, include_reason=True),
            FaithfulnessMetric(threshold=0.7, model=model, include_reason=True),
            ContextualRelevancyMetric(threshold=0.7, model=model, include_reason=True),
        ]

        if include_ground_truth_metrics:
            metrics.extend([
                ContextualPrecisionMetric(threshold=0.7, model=model, include_reason=True),
                ContextualRecallMetric(threshold=0.7, model=model, include_reason=True),
            ])

        return metrics

    # -----------------------------------------------------
    # Build DeepEval test cases from your RAG pipeline
    # -----------------------------------------------------
    async def construct_test_cases(self, project, num_questions=None) -> List[LLMTestCase]:
        test_cases = []

        questions = self.test_questions if num_questions is None else self.test_questions[:num_questions]

        for idx, q in enumerate(questions):
            question = q["question"]

            try:
                answer, full_prompt, chat_history, context = await self.nlp_controller.answer_rag_question(
                    project=project, query=question
                )
            except Exception as e:
                logger.error(f"Error answering question #{idx + 1}: {e}")
                continue

            if not answer:
                continue

            ctx = [doc.text for doc in context if getattr(doc, "text", None)]

            if not ctx:
                continue

            test_case = LLMTestCase(
                input=question,
                actual_output=answer,
                retrieval_context=ctx,
                expected_output=q.get("ground_truth", None)
            )

            test_cases.append(test_case)

        logger.info(f"Created {len(test_cases)} test cases.")
        return test_cases

    # -----------------------------------------------------
    # Run DeepEval evaluation
    # -----------------------------------------------------
    async def run_evaluation(self, project, num_questions=5):
        self.load_evaluation_data()

        test_cases = await self.construct_test_cases(project, num_questions)

        if not test_cases:
            return {"error": "No valid test cases found"}

        model = self.get_evaluation_model()
        metrics = self.create_metrics(model=model)

        try:
            evaluation_results = evaluate(
                test_cases=test_cases,
                metrics=metrics,
                async_config=AsyncConfig(
                    run_async=False, 
                    max_concurrent=1)
                )

            return  self.extract_metric_scores(evaluation_results["test_results"])

        except Exception as e:
            logger.error(f"DeepEval evaluation failed: {e}")
            return {"error": str(e)}

    # -----------------------------------------------------
    # Extract ONLY average metric scores using evaluation_results
    # -----------------------------------------------------
    def extract_metric_scores(test_results):
        """
        Extract only metric name, threshold, and score.
        
        Args:
            test_results (list): The "test_results" list from evaluation_results
        
        Returns:
            list: Clean list with metric name, threshold, score
        """
        
        cleaned_results = []

        for test_case in test_results:
            metrics_list = []
            
            for metric in test_case.get("metrics_data", []):
                metrics_list.append({
                    "name": metric.get("name"),
                    "threshold": metric.get("threshold"),
                    "score": metric.get("score")
                })
            
            cleaned_results.append({
                "test_case": test_case.get("name"),
                "metrics": metrics_list
            })
        
        return cleaned_results
