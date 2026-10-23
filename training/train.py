"""
train.py
=================================================
Training loop for CodeExplorer.
"""

import torch
from tqdm import tqdm
from utils.metrics import line_level_metrics
from utils.logger import setup_logger


def train_one_epoch(model, loader, optimizer, scheduler, loss_fn, device):
    model.train()
    total_loss = 0.0

    for batch in tqdm(loader, desc="Training"):
        optimizer.zero_grad()

        for k in batch:
            if torch.is_tensor(batch[k]):
                batch[k] = batch[k].to(device)

        outputs = model(batch)
        loss_dict = loss_fn(**outputs)

        loss_dict["total"].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()
        scheduler.step()

        total_loss += loss_dict["total"].item()

    return total_loss / len(loader)


@torch.no_grad()
def validate(model, loader, loss_fn, device):
    model.eval()
    total_loss = 0.0

    for batch in tqdm(loader, desc="Validation"):
        for k in batch:
            if torch.is_tensor(batch[k]):
                batch[k] = batch[k].to(device)

        outputs = model(batch)
        loss_dict = loss_fn(**outputs)
        total_loss += loss_dict["total"].item()

    return total_loss / len(loader)
