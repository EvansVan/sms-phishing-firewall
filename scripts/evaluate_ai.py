#!/usr/bin/env python
"""
AI Evaluation Script: Comprehensive Assessment of Phishing Detection Accuracy

This script evaluates the Gemini AI analyzer against a labeled dataset of 150 SMS messages
(75 phishing, 75 legitimate) and generates a detailed report with metrics, confusion matrix,
ROC curve, and per-category breakdown.

Usage:
    python scripts/evaluate_ai.py                    # Use default dataset
    python scripts/evaluate_ai.py --dataset custom.csv  # Use custom dataset
    python scripts/evaluate_ai.py --threshold 0.6    # Test different threshold

Output:
    - reports/evaluation_summary.json       - Metrics summary
    - reports/evaluation_predictions.json   - All predictions
    - reports/figures/confusion_matrix.png  - Confusion matrix heatmap
    - reports/figures/roc_curve.png         - ROC curve
    - reports/figures/metrics_comparison.png - Metric comparison
    - reports/figures/category_performance.png - Per-category breakdown
    - reports/EVALUATION_REPORT.md          - Full report in markdown
"""

import os
import sys
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import argparse
import time

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Import after env is loaded
from flask import Flask
from app import create_app
from app.services.gemini.analyzer import GeminiAnalyzer
from app.services.evaluation.metrics import EvaluationMetrics
from app.services.evaluation.visualizer import EvaluationVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIEvaluator:
    """Comprehensive AI evaluation framework."""

    def __init__(self, app: Flask, threshold: float = 0.5):
        """
        Initialize evaluator.

        Args:
            app: Flask application instance
            threshold: Classification threshold (0-1)
        """
        self.app = app
        self.threshold = threshold
        self.metrics = EvaluationMetrics(threshold=threshold)
        self.visualizer = EvaluationVisualizer()
        self.analyzer = None

    def load_dataset(self, filepath: str) -> List[Dict]:
        """
        Load evaluation dataset from CSV.

        Expected columns: id, text, actual_label, category
        where actual_label is 'phishing' or 'legitimate'

        Args:
            filepath: Path to CSV file

        Returns:
            List of message dictionaries
        """
        messages = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                messages.append({
                    'id': row['id'],
                    'text': row['text'],
                    'actual_label': row['actual_label'].lower() == 'phishing',
                    'category': row['category'].strip()
                })
        logger.info(f"Loaded {len(messages)} messages from {filepath}")
        return messages

    def evaluate(self, messages: List[Dict]) -> None:
        """
        Evaluate all messages and collect metrics.

        Args:
            messages: List of message dictionaries
        """
        logger.info(f"Starting evaluation with {len(messages)} messages...")

        start_time = time.time()
        successful = 0
        failed = 0

        with self.app.app_context():
            # Initialize analyzer in app context
            self.analyzer = GeminiAnalyzer()

            for idx, message in enumerate(messages, 1):
                try:
                    # Analyze message
                    result = self.analyzer.analyze_message(
                        message_text=message['text']
                    )

                    # Extract score (0-10 scale from Gemini)
                    raw_score = result.get('score', 0)
                    # Normalize to 0-1
                    predicted_score = min(raw_score / 10.0, 1.0)

                    # Record prediction
                    self.metrics.add_prediction(
                        actual_label=message['actual_label'],
                        predicted_score=predicted_score,
                        message_id=message['id'],
                        message_text=message['text'],
                        category=message['category']
                    )

                    successful += 1

                    # Progress indicator
                    if idx % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = idx / elapsed
                        remaining = (len(messages) - idx) / rate if rate > 0 else 0
                        logger.info(
                            f"Processed {idx}/{len(messages)} "
                            f"({elapsed:.1f}s, ~{remaining:.1f}s remaining)"
                        )

                except Exception as e:
                    logger.error(f"Failed to analyze message {message['id']}: {e}")
                    failed += 1
                    continue

        elapsed = time.time() - start_time
        logger.info(
            f"Evaluation complete: {successful} successful, {failed} failed "
            f"in {elapsed:.1f}s ({elapsed/len(messages):.2f}s per message)"
        )

    def generate_report(self, output_dir: str = "reports") -> Dict:
        """
        Generate comprehensive evaluation report.

        Args:
            output_dir: Directory to save reports and figures

        Returns:
            Summary dictionary
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        figures_path = output_path / "figures"
        figures_path.mkdir(exist_ok=True)

        logger.info(f"Generating reports in {output_dir}...")

        # Get metrics summary
        summary = self.metrics.get_summary()

        # Save JSON reports
        summary_file = output_path / "evaluation_summary.json"
        predictions_file = output_path / "evaluation_predictions.json"

        self.metrics.save_summary_json(str(summary_file))
        self.metrics.save_predictions_json(str(predictions_file))

        # Generate visualizations
        logger.info("Generating visualizations...")

        # Confusion matrix
        self.visualizer.plot_confusion_matrix(
            summary['confusion_matrix'],
            str(figures_path / "confusion_matrix.png")
        )

        # ROC curve
        self.visualizer.plot_roc_curve(
            self.metrics.all_labels,
            self.metrics.all_scores,
            str(figures_path / "roc_curve.png")
        )

        # Metrics comparison
        self.visualizer.plot_metrics_comparison(
            summary['metrics'],
            str(figures_path / "metrics_comparison.png")
        )

        # Category performance
        if summary['category_metrics']:
            self.visualizer.plot_category_performance(
                summary['category_metrics'],
                str(figures_path / "category_performance.png")
            )

        # Class distribution
        self.visualizer.plot_class_distribution(
            self.metrics.all_labels,
            str(figures_path / "class_distribution.png")
        )

        # Generate markdown report
        self._generate_markdown_report(output_path, summary)

        logger.info(f"Reports saved to {output_dir}")
        return summary

    def _generate_markdown_report(self, output_path: Path, summary: Dict) -> None:
        """Generate markdown evaluation report."""
        metrics = summary['metrics']
        cm = summary['confusion_matrix']

        # Top misclassifications
        misclassifications = self.metrics.get_misclassifications(limit=10)

        report = f"""# AI Evaluation Report: SMS Phishing Detection

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

This report evaluates the performance of the Gemini AI analyzer on {summary['total_predictions']} SMS messages:
- **Phishing (Positive):** {summary['phishing_count']} messages
- **Legitimate (Negative):** {summary['legitimate_count']} messages
- **Classification Threshold:** {summary['threshold']}

### Performance Grade

"""

        # Grade based on F1 score
        f1 = metrics['f1_score']
        if f1 >= 0.90:
            grade = "🟢 A+ (Excellent)"
        elif f1 >= 0.80:
            grade = "🟢 A (Very Good)"
        elif f1 >= 0.70:
            grade = "🟡 B (Good)"
        elif f1 >= 0.60:
            grade = "🟡 C (Acceptable)"
        else:
            grade = "🔴 D (Needs Improvement)"

        report += f"**Overall Grade: {grade}** (F1-Score: {f1:.4f})\n\n"

        report += f"""---

## Key Metrics

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| **Accuracy** | {metrics['accuracy']:.2%} | Overall correctness across all predictions |
| **Precision** | {metrics['precision']:.2%} | Of phishing alerts, how many are correct? |
| **Recall** | {metrics['recall']:.2%} | Of all phishing messages, how many caught? |
| **Specificity** | {metrics['specificity']:.2%} | Of legitimate messages, how many identified correctly? |
| **F1-Score** | {metrics['f1_score']:.4f} | Harmonic mean of precision & recall |
| **ROC-AUC** | {metrics['roc_auc']:.4f} | Overall ranking quality (0.5=random, 1.0=perfect) |
| **MCC** | {metrics['mcc']:.4f} | Matthews Correlation Coefficient (-1=opposite, 0=random, 1=perfect) |
| **False Positive Rate** | {metrics['false_positive_rate']:.2%} | Percentage of legitimate messages incorrectly flagged |

### Metric Explanations

**Accuracy** measures the percentage of all predictions that were correct. While useful, it can be misleading
on imbalanced datasets.

**Precision** answers: "When the model says phishing, how often is it right?" High precision means fewer false alarms.

**Recall** (Sensitivity) answers: "Of all phishing messages, how many did we catch?" High recall means we miss fewer phishing.

**F1-Score** is the harmonic mean of precision and recall. It's the best single metric for evaluating phishing detection
because it balances both false positives and false negatives.

**ROC-AUC** measures the model's ability to distinguish between phishing and legitimate across all thresholds.
1.0 = perfect, 0.5 = random guessing.

---

## Confusion Matrix

```
              Predicted
           Legitimate  Phishing
Actual L  |    {cm['true_negatives']:4d}   |   {cm['false_positives']:4d}   |
       P  |    {cm['false_negatives']:4d}   |   {cm['true_positives']:4d}   |
```

- **TP (True Positives):** {cm['true_positives']} - Phishing correctly detected
- **TN (True Negatives):** {cm['true_negatives']} - Legitimate correctly identified
- **FP (False Positives):** {cm['false_positives']} - Legitimate incorrectly flagged (False Alarms)
- **FN (False Negatives):** {cm['false_negatives']} - Phishing incorrectly passed (Missed Threats)

---

## Category Performance

"""

        # Category breakdown
        if summary['category_metrics']:
            report += "Performance across message categories:\n\n"
            report += "| Category | Count | Accuracy | Precision | Recall | F1-Score |\n"
            report += "|----------|-------|----------|-----------|--------|----------|\n"

            for cat_name, cat_metrics in summary['category_metrics'].items():
                report += (
                    f"| {cat_name} | {cat_metrics['count']} | "
                    f"{cat_metrics['accuracy']:.2%} | {cat_metrics['precision']:.2%} | "
                    f"{cat_metrics['recall']:.2%} | {cat_metrics['f1_score']:.4f} |\n"
                )
        else:
            report += "No category data available.\n"

        report += f"""

---

## Top Misclassifications

The model was most confident about {len(misclassifications)} errors:

"""

        for idx, pred in enumerate(misclassifications[:10], 1):
            actual = "PHISHING" if pred['actual_label'] else "LEGITIMATE"
            predicted = "PHISHING" if pred['predicted_label'] else "LEGITIMATE"
            confidence = pred['predicted_score']

            report += f"""
### {idx}. {actual} classified as {predicted} (confidence: {confidence:.1%})
- **Text:** "{pred['message_text'][:100]}{"..." if len(pred['message_text']) > 100 else ""}"
- **Category:** {pred['category']}
- **Score:** {pred['predicted_score']:.3f}
"""

        report += f"""

---

## Visualizations

The following charts have been generated (see figures/ directory):

1. **confusion_matrix.png** - Heatmap showing TP, TN, FP, FN
2. **roc_curve.png** - ROC curve showing threshold performance
3. **metrics_comparison.png** - Bar chart of all key metrics
4. **category_performance.png** - Performance breakdown by message category
5. **class_distribution.png** - Pie chart of phishing vs legitimate split

---

## Recommendations

"""

        # Generate recommendations based on metrics
        recommendations = []

        if metrics['recall'] < 0.85:
            recommendations.append(
                "⚠️ **Low Recall ({:.1%})**: The model is missing phishing messages. "
                "Consider lowering threshold or improving feature detection.".format(metrics['recall'])
            )

        if metrics['precision'] < 0.80:
            recommendations.append(
                "⚠️ **Low Precision ({:.1%})**: Too many false alarms. "
                "Consider raising threshold or improving filtering.".format(metrics['precision'])
            )

        if metrics['false_positive_rate'] > 0.10:
            recommendations.append(
                "⚠️ **High False Positive Rate ({:.1%})**: Legitimate messages are being flagged. "
                "This could frustrate users. Review threshold settings.".format(metrics['false_positive_rate'])
            )

        if metrics['f1_score'] >= 0.85:
            recommendations.append(
                "✅ **Strong Performance**: The model shows good balance between precision and recall. "
                "Current threshold settings are appropriate."
            )

        if not recommendations:
            recommendations.append("✅ Model performance is adequate. Continue monitoring with new data.")

        for rec in recommendations:
            report += f"- {rec}\n\n"

        report += f"""

---

## Technical Details

**Analyzer:** Gemini AI ({self.metrics.__class__.__name__})

**Evaluation Dataset:** 150 messages (50% phishing, 50% legitimate)

**Categories:**
- Credential Theft
- Financial Fraud
- Social Engineering
- General/Legitimate

**Average Inference Time:** {summary.get('avg_inference_time', 'N/A')}

**Model Version:** {os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')}

**Evaluation Date:** {datetime.now().isoformat()}

---

## Conclusion

The SMS Phishing Firewall demonstrates {grade.lower()} at detecting phishing messages with an F1-Score of {f1:.4f}.
This level of performance is suitable for {"deployment in production" if f1 >= 0.80 else "further testing and refinement"}.

Suggested next steps:
1. Validate on additional real-world data
2. Monitor false positive/negative rates in production
3. Re-train or fine-tune on misclassified examples
4. Gather user feedback on alert quality

"""

        # Write report
        report_file = output_path / "EVALUATION_REPORT.md"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Markdown report saved to {report_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Comprehensively evaluate SMS phishing detection AI'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='data/evaluation_dataset.csv',
        help='Path to evaluation dataset CSV'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Classification threshold (0-1, default 0.5)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='reports',
        help='Output directory for reports'
    )

    args = parser.parse_args()

    # Validate dataset exists
    if not Path(args.dataset).exists():
        logger.error(f"Dataset not found: {args.dataset}")
        sys.exit(1)

    # Create Flask app
    app = create_app()

    # Run evaluation
    evaluator = AIEvaluator(app, threshold=args.threshold)

    try:
        messages = evaluator.load_dataset(args.dataset)
        evaluator.evaluate(messages)
        summary = evaluator.generate_report(args.output)

        # Print summary
        print("\n" + "=" * 70)
        print(evaluator.metrics)
        print("=" * 70)
        print(f"\n📊 Reports saved to: {args.output}/")
        print(f"📄 Full report: {args.output}/EVALUATION_REPORT.md")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
