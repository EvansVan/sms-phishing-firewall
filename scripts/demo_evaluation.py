#!/usr/bin/env python
"""
Simple Evaluation Demo - Perfect for Live Presentations

Shows how the evaluation system works in a quick, easy-to-understand way.
Great for judges or stakeholders who want to see results immediately.

Usage:
    python scripts/demo_evaluation.py              # Full evaluation
    python scripts/demo_evaluation.py --quick      # Quick 10-message demo
"""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from app import create_app
from app.services.gemini.analyzer import GeminiAnalyzer
from app.services.evaluation.metrics import EvaluationMetrics
import csv
import argparse


def simple_demo():
    """Quick demo with 10 messages."""
    print("\n" + "="*70)
    print("SMS PHISHING DETECTION - QUICK DEMO")
    print("="*70)

    # Sample messages to test
    samples = [
        ("Hello! Your account has been suspended. Click here to verify: http://bit.ly/6h3jk", True, "credential_theft"),
        ("Hi Sarah, this is John from HR. Just confirming our meeting tomorrow at 2pm.", False, "general"),
        ("URGENT: Your bank account will be closed. Update payment info now: http://bank-verify.xyz", True, "financial_fraud"),
        ("Congratulations! You've won $1,000 voucher. Claim now: http://prize.click/abc123", True, "social_engineering"),
        ("Mom, can you send me $50? Having car trouble.", False, "general"),
        ("You have BT bill to pay. Click here: http://invoice.update-now.com/bills", True, "financial_fraud"),
        ("Thanks for shopping with us! Your order #12345 is confirmed.", False, "general"),
        ("ALERT: Unusual login from Nigeria. Verify identity: http://secure-verify.net", True, "credential_theft"),
        ("Hey, let's grab lunch tomorrow? I'm free after 3.", False, "general"),
        ("Limited offer! iPhone 13 for only $99. Buy now: http://cheap-iphone.site/offer?utm=flash", True, "social_engineering"),
    ]

    app = create_app()
    metrics = EvaluationMetrics(threshold=0.5)

    with app.app_context():
        analyzer = GeminiAnalyzer()

        print(f"\nAnalyzing {len(samples)} messages...\n")

        for idx, (text, actual_phishing, category) in enumerate(samples, 1):
            try:
                result = analyzer.analyze_message(text)
                score = min(result.get('score', 0) / 10.0, 1.0)

                predicted_phishing = score >= 0.5
                actual_label = "PHISHING" if actual_phishing else "LEGITIMATE"
                predicted_label = "PHISHING" if predicted_phishing else "LEGITIMATE"
                match = "✅" if actual_phishing == predicted_phishing else "❌"

                metrics.add_prediction(
                    actual_label=actual_phishing,
                    predicted_score=score,
                    message_id=str(idx),
                    message_text=text[:50],
                    category=category
                )

                print(f"{idx:2d}. {match} Actual: {actual_label:11s} | Predicted: {predicted_label:11s} (Confidence: {score:.2%})")
                print(f"    Message: {text[:60]}{'...' if len(text) > 60 else ''}")
                print()

            except Exception as e:
                print(f"{idx:2d}. ❌ Error: {e}\n")

    # Show summary
    print("\n" + "="*70)
    print(metrics)
    print("="*70)

    summary = metrics.get_summary()
    metrics_data = summary['metrics']

    print("\n🎯 SUMMARY:")
    print(f"   F1-Score:    {metrics_data['f1_score']:.4f}  ← Best overall metric")
    print(f"   Accuracy:    {metrics_data['accuracy']:.2%}")
    print(f"   Precision:   {metrics_data['precision']:.2%}  (Quality of alerts)")
    print(f"   Recall:      {metrics_data['recall']:.2%}  (Threat coverage)")
    print(f"   ROC-AUC:     {metrics_data['roc_auc']:.4f}  (Model quality)")

    # Performance grade
    f1 = metrics_data['f1_score']
    if f1 >= 0.90:
        grade = "🟢 A+ (Excellent)"
    elif f1 >= 0.80:
        grade = "🟢 A (Very Good)"
    elif f1 >= 0.70:
        grade = "🟡 B (Good)"
    else:
        grade = "🔴 C (Needs Improvement)"

    print(f"\nPerformance Grade: {grade}")
    print("\n" + "="*70)


def full_evaluation():
    """Run full evaluation on all 150 messages."""
    print("\nRunning full evaluation on 150 messages...")
    print("This will take a few minutes. Check reports/ folder for results.")
    os.system("python scripts/evaluate_ai.py")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Quick evaluation demo')
    parser.add_argument('--quick', action='store_true', help='Quick demo with 10 messages')
    parser.add_argument('--full', action='store_true', help='Full evaluation with 150 messages')

    args = parser.parse_args()

    if args.full:
        full_evaluation()
    else:
        # Default to quick demo
        simple_demo()


if __name__ == '__main__':
    main()
