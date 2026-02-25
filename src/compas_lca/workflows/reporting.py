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
    include_unknown_object_type: bool = True,
    unknown_label: str = "UNKNOWN_OBJECT_TYPE",
    sort_by: str = "median",  # "median" | "name" | "none"
    max_groups: int | None = None,
    dpi: int = 200,
) -> Path:
    """
    Aggregate Summary_*.csv by (object_type, layer_number) and plot:
      - bar height = sum(net_impact_median)
      - error bars = sum(net_impact_min) .. sum(net_impact_max)

    X labels:
      - if layer_number missing/blank: "<object_type>"
      - else: "<object_type> L<n>"

    Output:
      Box_Plot_{indicator}.png where indicator is parsed from Summary_{indicator}.csv
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

    # Normalize layer_number:
    # keep as string for labeling, but try to canonicalize like "1.0" -> "1"
    ln = df["layer_number"].astype(str).fillna("").str.strip()
    ln = ln.replace({"nan": "", "None": ""})

    def _canon_layer(s: str) -> str:
        if not s:
            return ""
        # Convert things like "1.0" to "1"
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

    # ---- Aggregate by (object_type, layer_number_norm) (SUM) ----
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
        if layer_s:
            return f"{obj_s} L{layer_s}"
        return obj_s

    grouped["x_label"] = [
        _make_label(o, l) for o, l in zip(grouped["object_type"], grouped["layer_number_norm"])
    ]

    # Sorting / slicing
    if sort_by == "median":
        grouped = grouped.sort_values("net_impact_median", ascending=False)
    elif sort_by == "name":
        grouped = grouped.sort_values("x_label", ascending=True)
    elif sort_by == "none":
        pass
    else:
        raise ValueError("sort_by must be one of: 'median', 'name', 'none'")

    if max_groups is not None:
        grouped = grouped.head(int(max_groups))

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

    # Figure size scales with number of groups
    width = max(10.0, 0.6 * len(grouped))
    height = 6.0
    fig, ax = plt.subplots(figsize=(width, height))

    ax.bar(x, y_median)
    ax.errorbar(x, y_median, yerr=yerr, fmt="none", capsize=3)

    ax.set_title(f"{indicator_name} — aggregated by object_type + layer (sum min/median/max)")
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
            sort_by="median",
            max_groups=None,  # e.g. 40 if you want to cap the plot
            dpi=300,
        )
        print(f"✅ Plot written: {out}")
    except Exception as e:
        print(f"❌ Plot generation failed: {e}")