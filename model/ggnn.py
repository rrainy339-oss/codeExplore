"""
ggnn.py
=================================================
Gated Graph Neural Network for structure-aware
line modeling.

Paper reference:
- Eq.(4): message passing
- Eq.(5): GRU update
"""

import torch
import torch.nn as nn
from torch_geometric.nn import MessagePassing


class GGNN(MessagePassing):
    def __init__(self, hidden_size, num_relations, steps=3, dropout=0.1):
        super().__init__(aggr="add")
        self.hidden_size = hidden_size
        self.steps = steps

        self.rel_weights = nn.ModuleList([
            nn.Linear(hidden_size, hidden_size, bias=False)
            for _ in range(num_relations)
        ])

        self.gru = nn.GRUCell(hidden_size, hidden_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, edge_index, edge_type):
        """
        x:           (N, D)
        edge_index:  (2, E)
        edge_type:   (E,)
        """
        h = x

        for _ in range(self.steps):
            m = torch.zeros_like(h)

            for r, W_r in enumerate(self.rel_weights):
                mask = edge_type == r
                if mask.sum() == 0:
                    continue

                edge_idx_r = edge_index[:, mask]
                m_r = self.propagate(edge_idx_r, x=h)
                m = m + W_r(m_r)

            h = self.gru(m, h)
            h = self.dropout(h)

        return h

    def message(self, x_j):
        return x_j
