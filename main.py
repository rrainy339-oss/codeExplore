"""
main.py
=================================================
Main entry for training and evaluation.
"""

import argparse
import torch
from config import build_config_from_args
from training.train import train_one_epoch, validate
from training.evaluate import evaluate
from utils.logger import setup_logger

# === Model imports ===
from model.codebert_encoder import CodeBERTEncoder
from model.ggnn import GGNN
from model.line_transformer import LineTransformer
from model.classification_heads import (
    LineClassifier,
    AttentionPooling,
    FileClassifier,
    CWEClassifier
)
from model.multitask_loss import MultiTaskLoss

# === Data ===
from data.linevul_loader import build_dataloader


class CodeExplorer(torch.nn.Module):
    def __init__(self, cfg):
        super().__init__()

        self.encoder = CodeBERTEncoder(cfg.pretrained_model, cfg.freeze_codebert)

        self.gnn = GGNN(
            cfg.hidden_size,
            cfg.gnn_num_relations,
            cfg.gnn_steps,
            cfg.gnn_dropout
        ) if cfg.use_gnn else None

        self.transformer = LineTransformer(
            cfg.hidden_size,
            cfg.num_transformer_layers,
            cfg.num_attention_heads,
            cfg.transformer_dropout
        ) if cfg.use_transformer else None

        self.line_cls = LineClassifier(cfg.hidden_size)
        self.attn_pool = AttentionPooling(cfg.hidden_size)
        self.file_cls = FileClassifier(cfg.hidden_size)
        self.cwe_cls = CWEClassifier(cfg.hidden_size, cfg.num_cwe_classes)

    def forward(self, batch):
        x = self.encoder(
            batch["input_ids"],
            batch["attention_mask"],
            batch["line_mask"]
        )

        if self.gnn:
            graph = batch["graph"]
            graph.x = x.view(-1, x.size(-1))
            graph.x = self.gnn(graph.x, graph.edge_index, graph.edge_type)
            x = graph.x.view(x.size())

        if self.transformer:
            x = self.transformer(x, batch["line_mask"])

        line_pred = self.line_cls(x)
        file_repr, _ = self.attn_pool(x, batch["line_mask"])
        file_pred = self.file_cls(file_repr)
        cwe_pred = self.cwe_cls(file_repr)

        return {
            "line_pred": line_pred,
            "file_pred": file_pred,
            "cwe_pred": cwe_pred,
            "line_label": batch["line_labels"],
            "file_label": batch["file_labels"],
            "cwe_label": batch["cwe_labels"],
            "line_mask": batch["line_mask"]
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["train", "evaluate"], required=True)
    parser.add_argument("--model_path", default=None)
    args = parser.parse_args()

    cfg = build_config_from_args(args)
    logger = setup_logger(cfg.log_dir, cfg.mode)

    model = CodeExplorer(cfg).to(cfg.device)
    loss_fn = MultiTaskLoss(
        cfg.lambda_line,
        cfg.lambda_file,
        cfg.lambda_cwe,
        cfg.line_pos_weight
    )

    if cfg.mode == "train":
        train_loader = build_dataloader(cfg, "train", cfg.project_split)
        val_loader = build_dataloader(cfg, "val", cfg.project_split, shuffle=False)

        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay
        )

        scheduler = torch.optim.lr_scheduler.LinearLR(
            optimizer,
            start_factor=0.1,
            total_iters=cfg.warmup_steps
        )

        best_val = float("inf")

        for epoch in range(cfg.epochs):
            train_loss = train_one_epoch(
                model, train_loader, optimizer, scheduler, loss_fn, cfg.device
            )
            val_loss = validate(
                model, val_loader, loss_fn, cfg.device
            )

            logger.info(f"Epoch {epoch}: train={train_loss:.4f}, val={val_loss:.4f}")

            if val_loss < best_val:
                best_val = val_loss
                torch.save(model.state_dict(), f"{cfg.checkpoint_dir}/best_model.pth")

    else:
        model.load_state_dict(torch.load(args.model_path))
        test_loader = build_dataloader(cfg, "test", cfg.project_split, shuffle=False)
        results = evaluate(model, test_loader, cfg.device)
        logger.info(results)


if __name__ == "__main__":
    main()
