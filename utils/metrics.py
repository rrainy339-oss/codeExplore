"""
metrics.py
=================================================
Evaluation metrics for CodeExplorer.

Includes:
- Line-level: Precision / Recall / F1 / AUC
- Ranking: Recall@20%, Effort@20%, IFA
- File-level: AUC / Accuracy
- CWE: Macro-F1
"""

import numpy as np
from sklearn.metrics import (
    precision_recall_fscore_support,
    roc_auc_score,
    accuracy_score,
    f1_score
)


# ---------- Line-level ----------
def line_level_metrics(y_true, y_pred, mask):
    y_true = y_true[mask == 1]
    y_pred_bin = (y_pred[mask == 1] >= 0.5).astype(int)

    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred_bin, average="binary", zero_division=0
    )

    auc = roc_auc_score(y_true, y_pred[mask == 1]) \
        if len(np.unique(y_true)) > 1 else 0.0

    return p, r, f1, auc


def recall_at_20_percent(scores, labels):
    k = max(1, int(0.2 * len(scores)))
    idx = np.argsort(scores)[::-1][:k]
    return int(labels[idx].sum() > 0)


def effort_at_20_percent(scores, labels):
    k = max(1, int(0.2 * len(scores)))
    idx = np.argsort(scores)[::-1][:k]
    return labels[idx].sum() / (labels.sum() + 1e-6)


def initial_false_alarm(scores, labels):
    idx = np.argsort(scores)[::-1]
    for i, j in enumerate(idx):
        if labels[j] == 1:
            return i
    return len(labels)


# ---------- File-level ----------
def file_level_metrics(y_true, y_pred):
    auc = roc_auc_score(y_true, y_pred) \
        if len(np.unique(y_true)) > 1 else 0.0
    acc = accuracy_score(y_true, (y_pred >= 0.5).astype(int))
    return auc, acc


# ---------- CWE ----------
def cwe_macro_f1(y_true, y_pred):
    y_pred_bin = (y_pred >= 0.5).astype(int)
    return f1_score(y_true, y_pred_bin, average="macro", zero_division=0)
