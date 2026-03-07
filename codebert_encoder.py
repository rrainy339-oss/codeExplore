"""
codebert_encoder.py
=================================================
Line-level token encoder using CodeBERT.

Paper reference:
- Eq.(1)-(3): [CLS] token used as line embedding
"""

import torch
import torch.nn as nn
from transformers import RobertaModel


class CodeBERTEncoder(nn.Module):
    def __init__(self, pretrained_model: str, freeze: bool = False):
        super().__init__()
        self.codebert = RobertaModel.from_pretrained(pretrained_model)

        if freeze:
            for p in self.codebert.parameters():
                p.requires_grad = False

        self.hidden_size = self.codebert.config.hidden_size

    def forward(self, input_ids, attention_mask, line_mask):
        """
        input_ids:      (B, L, T)
        attention_mask: (B, L, T)
        line_mask:      (B, L)
        """
        B, L, T = input_ids.size()

        input_ids = input_ids.view(B * L, T)
        attention_mask = attention_mask.view(B * L, T)

        outputs = self.codebert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        cls_embeddings = outputs.last_hidden_state[:, 0, :]
        cls_embeddings = cls_embeddings.view(B, L, -1)

        # Padding lines -> zero
        cls_embeddings = cls_embeddings * line_mask.unsqueeze(-1)

        return cls_embeddings
