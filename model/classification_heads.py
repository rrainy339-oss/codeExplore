"""
classification_heads.py
=================================================
Multi-task prediction heads.

Paper reference:
- Line-level: Eq.(7)
- File-level attention pooling: Eq.(8)-(10)
- CWE multi-label: Eq.(11)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class LineClassifier(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        return torch.sigmoid(self.fc2(x)).squeeze(-1)


class AttentionPooling(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.W = nn.Linear(hidden_size, hidden_size)
        self.v = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, x, mask):
        """
        x:    (B, L, D)
        mask: (B, L)
        """
        score = self.v(torch.tanh(self.W(x))).squeeze(-1)
        score = score.masked_fill(~mask, -1e9)

        alpha = torch.softmax(score, dim=1)
        pooled = torch.sum(alpha.unsqueeze(-1) * x, dim=1)
        return pooled, alpha


class FileClassifier(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        return torch.sigmoid(self.fc(x)).squeeze(-1)


class CWEClassifier(nn.Module):
    def __init__(self, hidden_size, num_classes):
        super().__init__()
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        return torch.sigmoid(self.fc(x))
