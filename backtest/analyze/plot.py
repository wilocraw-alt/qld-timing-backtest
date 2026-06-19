import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_equity(equities, out_png):
    """
    Plot all equity curves (log scale recommended for wide range).

    Parameters
    ----------
    equities : dict[str, pd.Series]
        Mapping of variant name -> equity Series.
    out_png : str
        Output file path.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    for name, series in equities.items():
        ax.plot(series.index, series.values, label=name, linewidth=0.8)
    ax.set_yscale("log")
    ax.set_title("Equity Curves (log scale)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend(loc="best", fontsize=7)
    ax.grid(True, alpha=0.3)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Equity plot saved: {out_png}")


def plot_drawdown(equities, out_png):
    """
    Plot drawdown curves for all variants.

    Parameters
    ----------
    equities : dict[str, pd.Series]
    out_png : str
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    for name, series in equities.items():
        cummax = series.cummax()
        dd = (series - cummax) / cummax
        ax.plot(dd.index, dd.values, label=name, linewidth=0.8)
    ax.set_title("Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.legend(loc="best", fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color="gray", linewidth=0.5)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Drawdown plot saved: {out_png}")
