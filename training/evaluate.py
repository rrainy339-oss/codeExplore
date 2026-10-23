"""
evaluate.py
=================================================
Evaluation on test set.
"""

import numpy as np
import torch
from tqdm import tqdm
from utils.metrics import (
    line_level_metrics,
    recall_at_20_percent,
    effort_at_20_percent,
    initial_false_alarm,
    file_level_metrics,
    cwe_macro_f1
)


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()

    line_scores, line_labels, line_masks = [], [], []
    file_scores, file_labels = [], []
    cwe_scores, cwe_labels = [], []

    for batch in tqdm(loader, desc="Evaluating"):
        for k in batch:
            if torch.is_tensor(batch[k]):
                batch[k] = batch[k].to(device)

        out = model(batch)

        line_scores.append(out["line_pred"].cpu().numpy())
        line_labels.append(batch["line_labels"].cpu().numpy())
        line_masks.append(batch["line_mask"].cpu().numpy())

        file_scores.append(out["file_pred"].cpu().numpy())
        file_labels.append(batch["file_labels"].cpu().numpy())

        cwe_scores.append(out["cwe_pred"].cpu().numpy())
        cwe_labels.append(batch["cwe_labels"].cpu().numpy())

    line_scores = np.concatenate(line_scores)
    line_labels = np.concatenate(line_labels)
    line_masks = np.concatenate(line_masks)

    p, r, f1, auc = line_level_metrics(line_labels, line_scores, line_masks)

    file_auc, file_acc = file_level_metrics(
        np.concatenate(file_labels),
        np.concatenate(file_scores)
    )

    cwe_f1 = cwe_macro_f1(
        np.concatenate(cwe_labels),
        np.concatenate(cwe_scores)
    )

    return {
        "line_P": p,
        "line_R": r,
        "line_F1": f1,
        "line_AUC": auc,
        "file_AUC": file_auc,
        "file_ACC": file_acc,
        "cwe_macro_F1": cwe_f1
    }
