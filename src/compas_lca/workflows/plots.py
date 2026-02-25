from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def plot_summary_errorbars_by_object_type_and_layer(
    summary_csv_path: str | Path,
    output_dir: str | Path,
    *,
    top_n: int = 25,          # <-- always top 25 by default
    include_unknown_object_type: bool = True,
    unknown_label: str = "UNKNOWN_OBJECT_TYPE",
    dpi: int = 200,
) -> Path:
    """
    Aggregate Summary_*.csv by (object_type, layer_number) and plot only the TOP N groups
    by summed net_impact_median.

    - bar height = sum(net_impact_median)
    - error bars = sum(net_impact_min) .. sum(net_impact_max)
    - x labels = "<object_type> L<n>" (layer present) else "<object_type>"
    - output filename = Box_Plot_{indicator}.png from Summary_{indicator}.csv
    """
    summary_path = Path(summary_csv_path).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary CSV not found: {summary_path}")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parse indicator from filename: Summary_GWPtotal.csv -> GWPtotal
    m = re.match(r"^Summary_(.+)\.csv$", summary_path.name)
    if not m:
        raise ValueError(
            f"Expected filename like 'Summary_<indicator>.csv', got: {summary_path.name}"
        )
    indicator_from_name = m.group(1)
    out_path = out_dir / f"Box_Plot_{indicator_from_name}.png"

    df = pd.read_csv(summary_path)

    required = {
        "object_type",
        "layer_number",
        "indicator_name",
        "indicator_unit",
        "net_impact_min",
        "net_impact_median",
        "net_impact_max",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in summary CSV: {sorted(missing)}")

    # Coerce numeric
    for c in ["net_impact_min", "net_impact_median", "net_impact_max"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Normalize object_type
    df["object_type"] = df["object_type"].astype(str).fillna("").str.strip()
    df.loc[df["object_type"].isin(["", "nan", "None"]), "object_type"] = np.nan

    if include_unknown_object_type:
        df["object_type"] = df["object_type"].fillna(unknown_label)
    else:
        df = df.dropna(subset=["object_type"])

    # Normalize layer_number to a stable string ("1.0" -> "1", blanks stay blank)
    ln = df["layer_number"].astype(str).fillna("").str.strip()
    ln = ln.replace({"nan": "", "None": ""})

    def _canon_layer(s: str) -> str:
        if not s:
            return ""
        try:
            f = float(s)
            i = int(f)
            if abs(f - i) < 1e-9:
                return str(i)
            return str(f)
        except Exception:
            return s

    df["layer_number_norm"] = ln.map(_canon_layer)

    # Drop rows without median
    df = df.dropna(subset=["net_impact_median"]).copy()
    if df.empty:
        raise ValueError("No plottable rows: 'net_impact_median' is missing/NaN for all rows.")

    # Axis label (assume one indicator per file)
    indicator_name = (
        str(df["indicator_name"].dropna().iloc[0])
        if df["indicator_name"].notna().any()
        else indicator_from_name
    )
    indicator_unit = (
        str(df["indicator_unit"].dropna().iloc[0])
        if df["indicator_unit"].notna().any()
        else ""
    )
    y_label = f"{indicator_name} [{indicator_unit}]" if indicator_unit else indicator_name

    # ---- Aggregate by (object_type, layer_number_norm): SUM ----
    grouped = (
        df.groupby(["object_type", "layer_number_norm"], dropna=False, as_index=False)
        .agg(
            net_impact_min=("net_impact_min", "sum"),
            net_impact_median=("net_impact_median", "sum"),
            net_impact_max=("net_impact_max", "sum"),
        )
    )

    # Build x labels
    def _make_label(obj: str, layer: str) -> str:
        obj_s = str(obj).strip()
        layer_s = str(layer).strip()
        return f"{obj_s} L{layer_s}" if layer_s else obj_s

    grouped["x_label"] = [
        _make_label(o, l) for o, l in zip(grouped["object_type"], grouped["layer_number_norm"])
    ]

    # ---- TOP N by median (always) ----
    if top_n is None:
        top_n = 25
    top_n = int(top_n)
    if top_n <= 0:
        raise ValueError("top_n must be a positive integer")

    grouped = grouped.sort_values("net_impact_median", ascending=False).head(top_n)

    # Prepare plot arrays
    x_labels = grouped["x_label"].astype(str).tolist()
    x = np.arange(len(grouped))

    y_median = grouped["net_impact_median"].to_numpy(dtype=float)
    y_min = grouped["net_impact_min"].to_numpy(dtype=float)
    y_max = grouped["net_impact_max"].to_numpy(dtype=float)

    # Error bars around median: (median-min, max-median)
    yerr_lower = np.clip(y_median - y_min, 0, np.inf)
    yerr_upper = np.clip(y_max - y_median, 0, np.inf)
    yerr = np.vstack([yerr_lower, yerr_upper])

    # Figure sizing for 25 items
    width = 14.0
    height = 6.0
    fig, ax = plt.subplots(figsize=(width, height))

    ax.bar(x, y_median)
    ax.errorbar(x, y_median, yerr=yerr, fmt="none", capsize=3)

    ax.set_title(f"{indicator_name} — top {len(grouped)} object_type+layer (by median)")
    ax.set_ylabel(y_label)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)

    return out_path

if __name__ == "__main__":
    SUMMARY_CSV = Path("/Users/wuitee/Documents/BRG/compas_lca/temp/projects/duplex/06_report/Summary_GWPtotal.csv")
    OUTPUT_DIR = Path("/Users/wuitee/Documents/BRG/compas_lca/temp/projects/duplex/06_report")

    try:
        out = plot_summary_errorbars_by_object_type_and_layer(
            summary_csv_path=SUMMARY_CSV,
            output_dir=OUTPUT_DIR,
            dpi=300,
            # top_n=25,  # optional override, but default is already 25
        )
        print(f"✅ Plot written: {out}")
    except Exception as e:
        print(f"❌ Plot generation failed: {e}")