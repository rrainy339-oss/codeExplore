"""
config.py
====================================
Global configuration for CodeExplorer
-------------------------------------
- Dataset paths
- Model hyperparameters
- Training hyperparameters
- Ablation switches
- Reproducibility (random seeds)

All parameters can be overridden via command-line arguments.
"""

import os
import torch
import random
import numpy as np
from dataclasses import dataclass, field


# ===============================
# Reproducibility
# ===============================
def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ===============================
# Main Config
# ===============================
@dataclass
class Config:
    # -------- Path --------
    data_root: str = "./linevul/"
    metadata_file: str = "metadata.csv"
    joern_path: str = "joern"  # joern executable
    cache_dir: str = "./cache/"
    checkpoint_dir: str = "./checkpoints/"
    log_dir: str = "./logs/"
    enable_cache: bool = True

    # -------- Dataset --------
    language: str = "c_cpp"
    max_lines: int = 400           # max lines per file
    max_tokens_per_line: int = 128 # max tokens per line
    num_cwe_classes: int = 9       # Big-Vul 常用 CWE 数量



    # -------- CodeBERT --------
    pretrained_model: str = "microsoft/codebert-base"
    hidden_size: int = 768
    freeze_codebert: bool = False  # 支持 partial fine-tuning

    # -------- GGNN --------
    use_gnn: bool = True
    gnn_steps: int = 3
    gnn_num_relations: int = 2      # control / data
    gnn_dropout: float = 0.1

    # -------- Line Transformer --------
    use_transformer: bool = True
    num_transformer_layers: int = 4
    num_attention_heads: int = 8
    transformer_dropout: float = 0.1

    # -------- Multi-task --------
    use_multitask: bool = False
    lambda_line: float = 1.0
    lambda_file: float = 1
    lambda_cwe: float = 0

    # -------- Training --------
    batch_size: int = 8
    eval_batch_size: int = 8
    epochs: int = 50
    learning_rate: float = 2e-5
    weight_decay: float = 1e-5
    warmup_steps: int = 1000
    gradient_clip: float = 1.0
    early_stop_patience: int = 5

    # -------- Class imbalance --------
    line_pos_weight: float = 5.0  # 用于 BCEWithLogitsLoss

    # -------- Runtime --------
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    num_workers: int = 4
    seed: int = 42

    # -------- Ablation --------
    ablation: str = "none"  # none | no_gnn | no_transformer | no_multitask

    def apply_ablation(self):
        if self.ablation == "no_gnn":
            self.use_gnn = False
        elif self.ablation == "no_transformer":
            self.use_transformer = False
        elif self.ablation == "no_multitask":
            self.use_multitask = False


# ===============================
# Helper
# ===============================
def build_config_from_args(args):
    cfg = Config(**vars(args))
    cfg.apply_ablation()

    os.makedirs(cfg.cache_dir, exist_ok=True)
    os.makedirs(cfg.checkpoint_dir, exist_ok=True)
    os.makedirs(cfg.log_dir, exist_ok=True)

    set_seed(cfg.seed)
    return cfg
