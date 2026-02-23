"""
Evaluation Visualization Module

Generates charts and graphs for evaluation reports:
- Confusion Matrix heatmap
- ROC Curve
- Metric comparison charts
- Category performance breakdown
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from sklearn.metrics import confusion_matrix, roc_curve, auc
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available. Visualizations will be skipped.")


class EvaluationVisualizer:
    """Generate evaluation visualizations."""

    def __init__(self, dpi: int = 100, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize visualizer.

        Args:
            dpi: Resolution for saved images
            style: Matplotlib style
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Visualizations require matplotlib and scikit-learn")
            return

        self.dpi = dpi
        try:
            plt.style.use(style)
        except Exception:
            pass  # Fall back to default style

    @staticmethod
    def plot_confusion_matrix(
        cm_values: Dict,
        output_path: str = None,
        figsize: tuple = (8, 6)
    ) -> Optional[str]:
        """
        Plot confusion matrix as heatmap.

        Args:
            cm_values: Dict with tp, tn, fp, fn
            output_path: Path to save figure
            figsize: Figure size

        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        tp = cm_values.get('true_positives', 0)
        tn = cm_values.get('true_negatives', 0)
        fp = cm_values.get('false_positives', 0)
        fn = cm_values.get('false_negatives', 0)

        cm = np.array([[tn, fp], [fn, tp]])

        fig, ax = plt.subplots(figsize=figsize)

        # Create heatmap
        im = ax.imshow(cm, cmap='Blues', aspect='auto')

        # Set labels
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(['Legitimate', 'Phishing'])
        ax.set_yticklabels(['Legitimate', 'Phishing'])
        ax.set_xlabel('Predicted Label', fontsize=12, fontweight='bold')
        ax.set_ylabel('Actual Label', fontsize=12, fontweight='bold')
        ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold', pad=20)

        # Add text annotations
        for i in range(2):
            for j in range(2):
                text_color = 'white' if cm[i, j] > cm.max() / 2 else 'black'
                ax.text(j, i, cm[i, j], ha='center', va='center',
                       color=text_color, fontsize=14, fontweight='bold')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Count', rotation=270, labelpad=20)

        # Add legend
        legend_text = (
            f'TP: {tp} | TN: {tn}\n'
            f'FP: {fp} | FN: {fn}\n'
            f'Total: {tp + tn + fp + fn}'
        )
        ax.text(0.5, -0.35, legend_text, ha='center', transform=ax.transAxes,
               fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            logger.info(f"Saved confusion matrix to {output_path}")

        plt.close()
        return output_path

    @staticmethod
    def plot_roc_curve(
        y_true: List[bool],
        y_scores: List[float],
        output_path: str = None,
        figsize: tuple = (8, 6)
    ) -> Optional[str]:
        """
        Plot ROC curve.

        Args:
            y_true: Actual labels
            y_scores: Predicted scores
            output_path: Path to save figure
            figsize: Figure size

        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        # Convert boolean to int
        y_true_int = [int(y) for y in y_true]

        # Calculate ROC curve
        fpr, tpr, thresholds = roc_curve(y_true_int, y_scores)
        roc_auc = auc(fpr, tpr)

        fig, ax = plt.subplots(figsize=figsize)

        # Plot ROC curve
        ax.plot(fpr, tpr, color='darkorange', lw=2.5,
               label=f'ROC Curve (AUC = {roc_auc:.4f})')

        # Plot diagonal (random classifier)
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--',
               label='Random Classifier (AUC = 0.5000)')

        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate', fontsize=12, fontweight='bold')
        ax.set_ylabel('True Positive Rate', fontsize=12, fontweight='bold')
        ax.set_title('ROC Curve - Phishing Detection', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='lower right', fontsize=11)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            logger.info(f"Saved ROC curve to {output_path}")

        plt.close()
        return output_path

    @staticmethod
    def plot_metrics_comparison(
        metrics: Dict[str, float],
        output_path: str = None,
        figsize: tuple = (10, 6)
    ) -> Optional[str]:
        """
        Plot bar chart comparing all metrics.

        Args:
            metrics: Dict of metric_name -> value
            output_path: Path to save figure
            figsize: Figure size

        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        # Filter only numeric metrics (0-1 range)
        plot_metrics = {
            k: v for k, v in metrics.items()
            if isinstance(v, (int, float)) and -1 <= v <= 1
        }

        fig, ax = plt.subplots(figsize=figsize)

        names = list(plot_metrics.keys())
        values = list(plot_metrics.values())
        colors = ['#2ecc71' if v >= 0.8 else '#f39c12' if v >= 0.6 else '#e74c3c'
                 for v in values]

        bars = ax.bar(names, values, color=colors, edgecolor='black', linewidth=1.5)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_ylim([0, 1.1])
        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title('Performance Metrics Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.axhline(y=0.8, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Excellent (0.8)')
        ax.axhline(y=0.6, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='Good (0.6)')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            logger.info(f"Saved metrics comparison to {output_path}")

        plt.close()
        return output_path

    @staticmethod
    def plot_category_performance(
        category_metrics: Dict[str, Dict],
        output_path: str = None,
        figsize: tuple = (12, 6)
    ) -> Optional[str]:
        """
        Plot performance metrics broken down by category.

        Args:
            category_metrics: Dict of category -> metrics dict
            output_path: Path to save figure
            figsize: Figure size

        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if not category_metrics:
            logger.warning("No category metrics to plot")
            return None

        categories = list(category_metrics.keys())
        accuracy_vals = [category_metrics[cat].get('accuracy', 0) for cat in categories]
        precision_vals = [category_metrics[cat].get('precision', 0) for cat in categories]
        recall_vals = [category_metrics[cat].get('recall', 0) for cat in categories]
        f1_vals = [category_metrics[cat].get('f1_score', 0) for cat in categories]

        x = np.arange(len(categories))
        width = 0.2

        fig, ax = plt.subplots(figsize=figsize)

        ax.bar(x - 1.5*width, accuracy_vals, width, label='Accuracy', color='#3498db')
        ax.bar(x - 0.5*width, precision_vals, width, label='Precision', color='#2ecc71')
        ax.bar(x + 0.5*width, recall_vals, width, label='Recall', color='#e74c3c')
        ax.bar(x + 1.5*width, f1_vals, width, label='F1-Score', color='#f39c12')

        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_xlabel('Message Category', fontsize=12, fontweight='bold')
        ax.set_title('Performance Metrics by Category', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend(loc='lower right')
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            logger.info(f"Saved category performance to {output_path}")

        plt.close()
        return output_path

    @staticmethod
    def plot_class_distribution(
        y_true: List[bool],
        output_path: str = None,
        figsize: tuple = (8, 6)
    ) -> Optional[str]:
        """
        Plot distribution of phishing vs legitimate messages.

        Args:
            y_true: Actual labels
            output_path: Path to save figure
            figsize: Figure size

        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        phishing_count = sum(1 for y in y_true if y)
        legitimate_count = sum(1 for y in y_true if not y)

        fig, ax = plt.subplots(figsize=figsize)

        labels = ['Phishing', 'Legitimate']
        sizes = [phishing_count, legitimate_count]
        colors = ['#e74c3c', '#2ecc71']
        explode = (0.05, 0)

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, explode=explode, textprops={'fontsize': 11, 'fontweight': 'bold'}
        )

        ax.set_title('Dataset Distribution', fontsize=14, fontweight='bold', pad=20)

        # Add count legend
        legend_labels = [f'{label}: {size}' for label, size in zip(labels, sizes)]
        ax.legend(legend_labels, loc='upper right')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            logger.info(f"Saved class distribution to {output_path}")

        plt.close()
        return output_path
