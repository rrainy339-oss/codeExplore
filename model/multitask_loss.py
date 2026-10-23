"""
multitask_loss.py
=================================================
Multi-task loss function.

Paper reference:
- Eq.(12): CWE loss
- Eq.(13): Total loss
"""

import torch
import torch.nn as nn


class MultiTaskLoss(nn.Module):
    def __init__(
        self,
        lambda_line=1.0,
        lambda_file=0.5,
        lambda_cwe=0.3,
        line_pos_weight=1.0
    ):
        super().__init__()

        self.lambda_line = lambda_line
        self.lambda_file = lambda_file
        self.lambda_cwe = lambda_cwe

        self.line_loss_fn = nn.BCELoss(reduction="none")
        self.file_loss_fn = nn.BCELoss()
        self.cwe_loss_fn = nn.BCELoss()

        self.line_pos_weight = line_pos_weight

    def forward(
        self,
        line_pred,
        line_label,
        line_mask,
        file_pred,
        file_label,
        cwe_pred,
        cwe_label
    ):
        # ---- Line-level loss (masked) ----
        line_loss = self.line_loss_fn(line_pred, line_label)
        line_loss = line_loss * line_mask

        # Class imbalance weighting
        weight = torch.ones_like(line_loss)
        weight[line_label == 1] = self.line_pos_weight
        line_loss = (line_loss * weight).sum() / line_mask.sum()

        # ---- File-level loss ----
        file_loss = self.file_loss_fn(file_pred, file_label)

        # ---- CWE multi-label loss ----
        cwe_loss = self.cwe_loss_fn(cwe_pred, cwe_label)

        total_loss = (
            self.lambda_line * line_loss +
            self.lambda_file * file_loss +
            self.lambda_cwe * cwe_loss
        )

        return {
            "total": total_loss,
            "line": line_loss.detach(),
            "file": file_loss.detach(),
            "cwe": cwe_loss.detach(),
        }
