"""
visualization.py
=================================================
Visualization utilities.
"""

import matplotlib.pyplot as plt


def plot_loss_curve(train_losses, val_losses, save_path):
    plt.figure()
    plt.plot(train_losses, label="train")
    plt.plot(val_losses, label="val")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig(save_path)
    plt.close()
