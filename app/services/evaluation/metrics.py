"""
AI Evaluation Metrics Module

Provides comprehensive evaluation metrics for phishing detection AI:
- Accuracy, Precision, Recall, F1-Score
- ROC-AUC, Confusion Matrix
- Performance per category
- Statistical analysis
"""

import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


@dataclass
class ConfusionMatrix:
    """Confusion matrix for binary classification."""
    true_positives: int = 0  # Phishing correctly identified
    true_negatives: int = 0  # Legitimate correctly identified
    false_positives: int = 0  # Legitimate incorrectly flagged as phishing
    false_negatives: int = 0  # Phishing missed

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """Pretty print confusion matrix."""
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        return (
            f"Confusion Matrix (Total: {total}):\n"
            f"  TP (Phishing detected correctly): {self.true_positives}\n"
            f"  TN (Legitimate correctly): {self.true_negatives}\n"
            f"  FP (False alarm): {self.false_positives}\n"
            f"  FN (Phishing missed): {self.false_negatives}"
        )


@dataclass
class ClassificationMetrics:
    """Classification metrics for a single class."""
    name: str
    count: int = 0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class EvaluationMetrics:
    """
    Comprehensive evaluation metrics for SMS phishing detection AI.

    Calculates:
    - Binary classification metrics (Accuracy, Precision, Recall, F1)
    - ROC-AUC (Area Under the Curve)
    - Per-category performance
    - Confusion matrix
    - Statistical summaries
    """

    def __init__(self, threshold: float = 0.5):
        """
        Initialize metrics calculator.

        Args:
            threshold: Score threshold for positive classification (0-1)
                      Scores >= threshold are classified as phishing
        """
        self.threshold = threshold
        self.confusion_matrix = ConfusionMatrix()
        self.all_scores: List[float] = []
        self.all_labels: List[bool] = []
        self.all_categories: List[str] = []
        self.predictions: List[Dict] = []
        self.category_metrics: Dict[str, ClassificationMetrics] = defaultdict(
            lambda: ClassificationMetrics(name="")
        )

    def add_prediction(
        self,
        actual_label: bool,
        predicted_score: float,
        message_id: str = None,
        message_text: str = None,
        category: str = "unknown"
    ) -> None:
        """
        Add a prediction for evaluation.

        Args:
            actual_label: True if actual label is phishing, False if legitimate
            predicted_score: Model's confidence score (0-1)
            message_id: Optional message identifier
            message_text: Optional message text for analysis
            category: Category of message (credential_theft, financial, social_eng, etc.)
        """
        predicted_label = predicted_score >= self.threshold

        # Update confusion matrix
        if actual_label and predicted_label:
            self.confusion_matrix.true_positives += 1
        elif not actual_label and not predicted_label:
            self.confusion_matrix.true_negatives += 1
        elif not actual_label and predicted_label:
            self.confusion_matrix.false_positives += 1
        else:  # actual_label and not predicted_label
            self.confusion_matrix.false_negatives += 1

        # Track all scores and labels for ROC-AUC
        self.all_scores.append(predicted_score)
        self.all_labels.append(actual_label)
        self.all_categories.append(category)

        # Store prediction
        self.predictions.append({
            "message_id": message_id,
            "message_text": message_text,
            "actual_label": actual_label,
            "predicted_score": predicted_score,
            "predicted_label": predicted_label,
            "correct": actual_label == predicted_label,
            "category": category
        })

    def accuracy(self) -> float:
        """
        Calculate accuracy: (TP + TN) / Total

        Best for: Balanced datasets
        Range: 0-1 (higher is better)
        """
        total = sum([
            self.confusion_matrix.true_positives,
            self.confusion_matrix.true_negatives,
            self.confusion_matrix.false_positives,
            self.confusion_matrix.false_negatives
        ])
        if total == 0:
            return 0.0
        return (
            self.confusion_matrix.true_positives + self.confusion_matrix.true_negatives
        ) / total

    def precision(self) -> float:
        """
        Calculate precision: TP / (TP + FP)

        Meaning: Of all phishing alerts, how many were actually phishing?
        Best for: When false positives are costly
        Range: 0-1 (higher is better)
        """
        denominator = (
            self.confusion_matrix.true_positives + self.confusion_matrix.false_positives
        )
        if denominator == 0:
            return 0.0
        return self.confusion_matrix.true_positives / denominator

    def recall(self) -> float:
        """
        Calculate recall (sensitivity/TPR): TP / (TP + FN)

        Meaning: Of all actual phishing messages, how many did we catch?
        Best for: When missing phishing is costly
        Range: 0-1 (higher is better)
        """
        denominator = (
            self.confusion_matrix.true_positives + self.confusion_matrix.false_negatives
        )
        if denominator == 0:
            return 0.0
        return self.confusion_matrix.true_positives / denominator

    def specificity(self) -> float:
        """
        Calculate specificity (TNR): TN / (TN + FP)

        Meaning: Of all legitimate messages, how many correctly identified?
        Range: 0-1 (higher is better)
        """
        denominator = (
            self.confusion_matrix.true_negatives + self.confusion_matrix.false_positives
        )
        if denominator == 0:
            return 0.0
        return self.confusion_matrix.true_negatives / denominator

    def f1_score(self) -> float:
        """
        Calculate F1-Score: 2 * (Precision * Recall) / (Precision + Recall)

        Meaning: Harmonic mean of precision and recall
        Best for: Imbalanced datasets (phishing detection is imbalanced)
        Range: 0-1 (higher is better)
        """
        precision = self.precision()
        recall = self.recall()
        denominator = precision + recall
        if denominator == 0:
            return 0.0
        return 2 * (precision * recall) / denominator

    def false_positive_rate(self) -> float:
        """
        Calculate FPR: FP / (FP + TN)

        Meaning: Of all legitimate messages, how many incorrectly flagged?
        Range: 0-1 (lower is better)
        """
        return 1.0 - self.specificity()

    def roc_auc(self) -> float:
        """
        Calculate ROC-AUC (Area Under the Receiver Operating Characteristic Curve)

        Meaning: Probability that model ranks a random phishing higher than legitimate
        Range: 0-1 (higher is better)
        0.5 = random guessing, 1.0 = perfect classification
        """
        if len(self.all_scores) == 0:
            return 0.0

        # Separate positive and negative scores
        positive_scores = [
            score for score, label in zip(self.all_scores, self.all_labels) if label
        ]
        negative_scores = [
            score for score, label in zip(self.all_scores, self.all_labels) if not label
        ]

        if len(positive_scores) == 0 or len(negative_scores) == 0:
            return 0.0

        # Count pairs where positive score > negative score
        correct_pairs = 0
        for pos_score in positive_scores:
            for neg_score in negative_scores:
                if pos_score > neg_score:
                    correct_pairs += 1

        total_pairs = len(positive_scores) * len(negative_scores)
        return correct_pairs / total_pairs if total_pairs > 0 else 0.0

    def matthews_correlation_coefficient(self) -> float:
        """
        Calculate MCC: (-1 to +1, 0 = no better than random)

        Meaning: Correlation between actual and predicted labels
        Range: -1 to 1 (higher is better, 0 = random)
        Best for: Imbalanced datasets, comparable across thresholds
        """
        tp = self.confusion_matrix.true_positives
        tn = self.confusion_matrix.true_negatives
        fp = self.confusion_matrix.false_positives
        fn = self.confusion_matrix.false_negatives

        numerator = (tp * tn) - (fp * fn)
        denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))

        if denominator == 0:
            return 0.0
        return numerator / denominator

    def per_category_metrics(self) -> Dict[str, ClassificationMetrics]:
        """
        Calculate metrics broken down by message category.

        Returns:
            Dict mapping category name to ClassificationMetrics
        """
        categories = set(self.all_categories)

        for category in categories:
            category_preds = [
                p for p in self.predictions if p["category"] == category
            ]

            if not category_preds:
                continue

            tp = sum(1 for p in category_preds if p["actual_label"] and p["predicted_label"])
            tn = sum(1 for p in category_preds if not p["actual_label"] and not p["predicted_label"])
            fp = sum(1 for p in category_preds if not p["actual_label"] and p["predicted_label"])
            fn = sum(1 for p in category_preds if p["actual_label"] and not p["predicted_label"])

            total = tp + tn + fp + fn
            accuracy = (tp + tn) / total if total > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            self.category_metrics[category] = ClassificationMetrics(
                name=category,
                count=total,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                tp=tp,
                fp=fp,
                fn=fn,
                tn=tn
            )

        return self.category_metrics

    def get_summary(self) -> Dict:
        """
        Get comprehensive summary of all metrics.

        Returns:
            Dictionary with all calculated metrics
        """
        return {
            "total_predictions": len(self.predictions),
            "phishing_count": sum(1 for p in self.predictions if p["actual_label"]),
            "legitimate_count": sum(1 for p in self.predictions if not p["actual_label"]),
            "threshold": self.threshold,
            "metrics": {
                "accuracy": round(self.accuracy(), 4),
                "precision": round(self.precision(), 4),
                "recall": round(self.recall(), 4),
                "specificity": round(self.specificity(), 4),
                "f1_score": round(self.f1_score(), 4),
                "false_positive_rate": round(self.false_positive_rate(), 4),
                "roc_auc": round(self.roc_auc(), 4),
                "mcc": round(self.matthews_correlation_coefficient(), 4),
            },
            "confusion_matrix": self.confusion_matrix.to_dict(),
            "category_metrics": {
                cat: metrics.to_dict()
                for cat, metrics in self.per_category_metrics().items()
            }
        }

    def get_misclassifications(self, limit: int = 10) -> List[Dict]:
        """
        Get incorrectly classified predictions.

        Args:
            limit: Maximum number of misclassifications to return

        Returns:
            List of incorrect predictions sorted by most confident errors
        """
        misclassified = [p for p in self.predictions if not p["correct"]]
        # Sort by how confident the model was in the wrong answer
        misclassified.sort(
            key=lambda p: max(p["predicted_score"], 1 - p["predicted_score"]),
            reverse=True
        )
        return misclassified[:limit]

    def save_summary_json(self, filepath: str) -> None:
        """Save evaluation summary to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)
        logger.info(f"Saved evaluation summary to {filepath}")

    def save_predictions_json(self, filepath: str) -> None:
        """Save all predictions to JSON file for detailed analysis."""
        with open(filepath, 'w') as f:
            json.dump(self.predictions, f, indent=2)
        logger.info(f"Saved predictions to {filepath}")

    def __str__(self) -> str:
        """Pretty print summary."""
        summary = self.get_summary()
        metrics = summary["metrics"]

        return (
            "=" * 60 + "\n"
            "AI EVALUATION REPORT\n"
            "=" * 60 + "\n"
            f"Total Predictions: {summary['total_predictions']}\n"
            f"Phishing (Positive): {summary['phishing_count']}\n"
            f"Legitimate (Negative): {summary['legitimate_count']}\n"
            f"Threshold: {self.threshold}\n\n"
            "METRICS:\n"
            f"  Accuracy:      {metrics['accuracy']:.2%}  (Overall correctness)\n"
            f"  Precision:     {metrics['precision']:.2%}  (Of flagged, how many phishing?)\n"
            f"  Recall:        {metrics['recall']:.2%}  (Of phishing, how many caught?)\n"
            f"  Specificity:   {metrics['specificity']:.2%}  (Of legitimate, how many correct?)\n"
            f"  F1-Score:      {metrics['f1_score']:.4f}  (Harmonic mean)\n"
            f"  ROC-AUC:       {metrics['roc_auc']:.4f}  (Ranking quality)\n"
            f"  MCC:           {metrics['mcc']:.4f}  (Correlation)\n"
            f"  FPR:           {metrics['false_positive_rate']:.2%}  (False alarm rate)\n\n"
            + str(self.confusion_matrix) + "\n"
            "=" * 60
        )
