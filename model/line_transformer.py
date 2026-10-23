"""
line_transformer.py
=================================================
Line-level Transformer encoder for global context.

Paper reference:
- Eq.(6): Multi-head self-attention
"""

import torch
import torch.nn as nn


class LineTransformer(nn.Module):
    def __init__(self, hidden_size, num_layers, num_heads, dropout):
        super().__init__()

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            dropout=dropout,
            batch_first=True
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

    def forward(self, x, line_mask):
        """
        x:         (B, L, D)
        line_mask: (B, L)
        """
        key_padding_mask = ~line_mask
        out = self.encoder(x, src_key_padding_mask=key_padding_mask)
        return out
