from pathlib import Path

import hashlib

import colorsys

import numpy as np

import pandas as pd

import seaborn as sns

import plotly.graph_objects as go

import matplotlib

import matplotlib.pyplot as plt

from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from typing import Callable
# --------------------------------
# TOP 25 IMPACTS BY OBJECT TYPE AND LAYER
# --------------------------------
def top25_impacts(
    aggregated_csv_path: str | Path,
    output_dir: str | Path,
) -> None:
    """
    Plot from a CSV that already has exactly one row per (object_type, layer_number).

    Required columns:
      object_type, layer_number, indicator_name, indicator_unit,
      Total_net_impact_min, Total_net_impact_median, Total_net_impact_max

    Returns:
      Path to the written PNG.
    """

    # ---- constants (formerly parameters) ----
    TOP_N: int = 25
    INCLUDE_UNKNOWN_OBJECT_TYPE: bool = True
    UNKNOWN_LABEL: str = "UNKNOWN_OBJECT_TYPE"
    DPI: int = 300

    csv_path = Path(aggregated_csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    out_path = output_dir / f"top25_impacts.png"

    df = pd.read_csv(csv_path)

    required = {
        "object_type",
        "layer_number",
        "indicator_name",
        "indicator_unit",
        "Total_net_impact_min",
        "Total_net_impact_median",
        "Total_net_impact_max",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in CSV: {sorted(missing)}")

    # Coerce numeric
    numeric_cols = ["Total_net_impact_min", "Total_net_impact_median", "Total_net_impact_max"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Drop rows with missing median
    df = df.dropna(subset=["Total_net_impact_median"]).copy()
    if df.empty:
        raise ValueError("No plottable rows: 'Total_net_impact_median' is missing/NaN for all rows.")

    # Normalize object_type
    df["object_type"] = df["object_type"].astype(str).fillna("").str.strip()
    df.loc[df["object_type"].isin(["", "nan", "None"]), "object_type"] = np.nan
    if INCLUDE_UNKNOWN_OBJECT_TYPE:
        df["object_type"] = df["object_type"].fillna(UNKNOWN_LABEL)
    else:
        df = df.dropna(subset=["object_type"])

    # Normalize layer_number to stable string
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

    # Indicator label (assume one indicator per file)
    indicator_name = (
        str(df["indicator_name"].dropna().iloc[0])
        if df["indicator_name"].notna().any()
        else csv_path.stem
    )
    indicator_unit = (
        str(df["indicator_unit"].dropna().iloc[0])
        if df["indicator_unit"].notna().any()
        else ""
    )
    y_label = f"{indicator_name} [{indicator_unit}]" if indicator_unit else indicator_name

    grouped = df.copy()

    # Build x labels and the "has layer?" group for coloring/legend
    def _make_label(obj: str, layer: str) -> str:
        obj_s = str(obj).strip()
        layer_s = str(layer).strip()
        return f"{obj_s} L{layer_s}" if layer_s else obj_s

    grouped["x_label"] = [
        _make_label(o, l) for o, l in zip(grouped["object_type"], grouped["layer_number_norm"])
    ]

    grouped["layer_group"] = np.where(
        grouped["layer_number_norm"].astype(str).str.strip().eq(""),
        "Object type elements",
        "Object type layers",
    )

    # Top N by median
    if TOP_N <= 0:
        raise ValueError("TOP_N must be a positive integer")
    grouped = grouped.sort_values("Total_net_impact_median", ascending=False).head(TOP_N)

    # Preserve order on x axis (seaborn uses categorical ordering)
    x_order = grouped["x_label"].astype(str).tolist()
    grouped["x_label"] = pd.Categorical(grouped["x_label"], categories=x_order, ordered=True)

    # Arrays for errorbars (match the plotted order)
    grouped = grouped.sort_values("x_label")
    x_labels = grouped["x_label"].astype(str).tolist()
    x = np.arange(len(grouped))

    y_median = grouped["Total_net_impact_median"].to_numpy(dtype=float)
    y_min = grouped["Total_net_impact_min"].to_numpy(dtype=float)
    y_max = grouped["Total_net_impact_max"].to_numpy(dtype=float)

    yerr_lower = np.clip(y_median - y_min, 0, np.inf)
    yerr_upper = np.clip(y_max - y_median, 0, np.inf)
    yerr = np.vstack([yerr_lower, yerr_upper])

    # --- Plot ---
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14.0, 6.0))

    sns.barplot(
        data=grouped,
        x="x_label",
        y="Total_net_impact_median",
        hue="layer_group",
        hue_order=["Object type elements", "Object type layers"],
        estimator=np.mean,
        errorbar=None,
        dodge=False,
        ax=ax,
    )

    # color xticklabels by the bar group color
    handles, labels = ax.get_legend_handles_labels()
    color_map = {lab: h.get_facecolor() for h, lab in zip(handles, labels)}
    x_to_group = grouped.set_index("x_label")["layer_group"].to_dict()
    for tl in ax.get_xticklabels():
        xl = tl.get_text()
        grp = x_to_group.get(xl)
        if grp in color_map:
            tl.set_color(color_map[grp])

    # Error bars
    ax.errorbar(
        x,
        y_median,
        yerr=yerr,
        fmt="none",
        ecolor="black",
        elinewidth=1.0,
        capsize=3,
        capthick=1.0,
        zorder=5,
    )

    ax.set_title(f"{indicator_name} — Top {len(grouped)} ObjectType net emissions (by median)")
    ax.set_ylabel(y_label)
    ax.set_xlabel("")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=8)

    ax.legend(title="", loc="best", frameon=True)

    fig.tight_layout()
    fig.savefig(out_path, dpi=DPI)
    plt.close(fig)

def plot_total_emissions_by_stage(csv_path: str | Path, output_dir: str | Path) -> None:
    """
    Reads an element-level CSV, sums net impacts across all rows per stage,
    and plots one bar per stage: height = summed median, error bar = (summed min .. summed max).

    Only arguments:
      - csv_path: path to input CSV
      - output_dir: directory to write the output figure

    Returns:
      Path to the written figure.
    """

    # ---- constants (frozen config) ----
    OUTPUT_FILENAME = "total_emissions_by_stage.png"
    STAGES = ["A1-A3", "A4", "A5", "C1", "C2", "C3", "C4", "D", "Total"]
    DPI = 300
    FIGSIZE = (12, 6)

    def _col(stage: str, stat: str) -> str:
        # stat in {"min", "median", "max"}
        if stage == "A1-A3":
            return f"A1-A3_net_impact_{stat}"
        return f"{stage}_net_impact_{stat}"

    def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> None:
        for c in columns:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

    def _a1a3_has_data(df: pd.DataFrame) -> bool:
        cols = [_col("A1-A3", s) for s in ("min", "median", "max")]
        existing = [c for c in cols if c in df.columns]
        if not existing:
            return False
        return any(df[c].notna().any() for c in existing)

    def _build_a1a3_from_components(df: pd.DataFrame) -> None:
        # Create/overwrite A1-A3_{min,median,max} = A1 + A2 + A3 (row-wise), NaNs treated as 0.
        for stat in ("min", "median", "max"):
            target = _col("A1-A3", stat)
            parts = [f"A1_net_impact_{stat}", f"A2_net_impact_{stat}", f"A3_net_impact_{stat}"]

            for p in parts:
                if p not in df.columns:
                    df[p] = np.nan

            df[target] = df[parts].fillna(0).sum(axis=1)

    csv_path = Path(csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path, low_memory=False)

    # Coerce all potentially relevant numeric columns
    numeric_cols: list[str] = []
    numeric_cols += [_col("A1-A3", s) for s in ("min", "median", "max")]
    for st in ("A1", "A2", "A3"):
        numeric_cols += [f"{st}_net_impact_{s}" for s in ("min", "median", "max")]
    for st in ("A4", "A5", "C1", "C2", "C3", "C4", "D", "Total"):
        numeric_cols += [_col(st, s) for s in ("min", "median", "max")]

    _coerce_numeric(df, numeric_cols)

    # If A1-A3 missing/unusable, compute it from A1+A2+A3
    if not _a1a3_has_data(df):
        _build_a1a3_from_components(df)

    # Aggregate sums across all rows for each stage/stat
    rows: list[dict[str, object]] = []
    for st in STAGES:
        cmin, cmed, cmax = _col(st, "min"), _col(st, "median"), _col(st, "max")

        total_min = df[cmin].sum(skipna=True) if cmin in df.columns else np.nan
        total_med = df[cmed].sum(skipna=True) if cmed in df.columns else np.nan
        total_max = df[cmax].sum(skipna=True) if cmax in df.columns else np.nan

        rows.append({"stage": st, "min": total_min, "median": total_med, "max": total_max})

    agg = pd.DataFrame(rows).dropna(subset=["median"], how="all").reset_index(drop=True)
    if agg.empty or agg["median"].notna().sum() == 0:
        raise ValueError("No plottable data: all stage medians are NaN/missing.")

    # Optional unit
    unit: str | None = None
    if "indicator_unit" in df.columns:
        u = df["indicator_unit"].dropna().astype(str)
        unit = u.iloc[0] if len(u) else None

    # Plot
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=FIGSIZE)

    order = [s for s in STAGES if s in set(agg["stage"])]
    sns.barplot(data=agg, x="stage", y="median", order=order, ax=ax, errorbar=None)

    # Align agg to plotted order
    agg_ordered = agg.set_index("stage").loc[order].reset_index()

    lower = (agg_ordered["median"] - agg_ordered["min"]).to_numpy(dtype=float)
    upper = (agg_ordered["max"] - agg_ordered["median"]).to_numpy(dtype=float)
    lower = np.where(np.isfinite(lower), lower, 0.0)
    upper = np.where(np.isfinite(upper), upper, 0.0)
    yerr = np.vstack([lower, upper])

    x_positions = np.arange(len(order))
    ax.errorbar(
        x=x_positions,
        y=agg_ordered["median"].to_numpy(dtype=float),
        yerr=yerr,
        fmt="none",
        capsize=5,
        linewidth=1.5,
        color="black",
        zorder=10,
    )

    ylabel = "Total emissions" + (f" ({unit})" if unit else "")
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Stage")
    ax.set_title("Total emissions by life cycle stage (median with min/max error bars)")
    plt.tight_layout()

    out_path = out_dir / OUTPUT_FILENAME
    fig.savefig(out_path, dpi=DPI)
    plt.close(fig)


# --------------------------------
# ALL TOTAL EMISSIONS BY STAGE (BAR + ERRORBAR)
# --------------------------------
def total_emissions(csv_path: str | Path, output_dir: str | Path) -> None:
    """
    Reads an element-level CSV, sums net impacts across all rows per stage,
    and plots one bar per stage: height = summed median, error bar = (summed min .. summed max).

    Y-axis label is derived from indicator_name (+ indicator_unit if present).

    Only arguments:
      - csv_path: path to input CSV
      - output_dir: directory to write the output figure
    """

    # ---- constants (frozen config) ----
    OUTPUT_FILENAME = "total_emissions.png"
    STAGES = ["A1-A3", "A4", "A5", "C1", "C2", "C3", "C4", "D", "Total"]
    DPI = 300
    FIGSIZE = (12, 6)

    def _col(stage: str, stat: str) -> str:
        if stage == "A1-A3":
            return f"A1-A3_net_impact_{stat}"
        return f"{stage}_net_impact_{stat}"

    def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> None:
        for c in columns:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

    def _a1a3_has_data(df: pd.DataFrame) -> bool:
        cols = [_col("A1-A3", s) for s in ("min", "median", "max")]
        existing = [c for c in cols if c in df.columns]
        if not existing:
            return False
        return any(df[c].notna().any() for c in existing)

    def _build_a1a3_from_components(df: pd.DataFrame) -> None:
        # Create/overwrite A1-A3_{min,median,max} = A1 + A2 + A3 (row-wise), NaNs treated as 0.
        for stat in ("min", "median", "max"):
            target = _col("A1-A3", stat)
            parts = [f"A1_net_impact_{stat}", f"A2_net_impact_{stat}", f"A3_net_impact_{stat}"]

            for p in parts:
                if p not in df.columns:
                    df[p] = np.nan

            df[target] = df[parts].fillna(0).sum(axis=1)

    csv_path = Path(csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path, low_memory=False)

    # --- indicator label (preferred over "Total emissions") ---
    indicator_name = (
        str(df["indicator_name"].dropna().iloc[0]).strip()
        if "indicator_name" in df.columns and df["indicator_name"].notna().any()
        else "Indicator"
    )
    indicator_unit = (
        str(df["indicator_unit"].dropna().iloc[0]).strip()
        if "indicator_unit" in df.columns and df["indicator_unit"].notna().any()
        else ""
    )
    y_label = f"{indicator_name} [{indicator_unit}]" if indicator_unit else indicator_name

    # Coerce all potentially relevant numeric columns
    numeric_cols: list[str] = []
    numeric_cols += [_col("A1-A3", s) for s in ("min", "median", "max")]
    for st in ("A1", "A2", "A3"):
        numeric_cols += [f"{st}_net_impact_{s}" for s in ("min", "median", "max")]
    for st in ("A4", "A5", "C1", "C2", "C3", "C4", "D", "Total"):
        numeric_cols += [_col(st, s) for s in ("min", "median", "max")]

    _coerce_numeric(df, numeric_cols)

    # If A1-A3 missing/unusable, compute it from A1+A2+A3
    if not _a1a3_has_data(df):
        _build_a1a3_from_components(df)

    # Aggregate sums across all rows for each stage/stat
    rows: list[dict[str, object]] = []
    for st in STAGES:
        cmin, cmed, cmax = _col(st, "min"), _col(st, "median"), _col(st, "max")

        total_min = df[cmin].sum(skipna=True) if cmin in df.columns else np.nan
        total_med = df[cmed].sum(skipna=True) if cmed in df.columns else np.nan
        total_max = df[cmax].sum(skipna=True) if cmax in df.columns else np.nan

        rows.append({"stage": st, "min": total_min, "median": total_med, "max": total_max})

    agg = pd.DataFrame(rows).dropna(subset=["median"], how="all").reset_index(drop=True)
    if agg.empty or agg["median"].notna().sum() == 0:
        raise ValueError("No plottable data: all stage medians are NaN/missing.")

    # Plot
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=FIGSIZE)

    order = [s for s in STAGES if s in set(agg["stage"])]
    sns.barplot(data=agg, x="stage", y="median", order=order, ax=ax, errorbar=None)

    # Align agg to plotted order
    agg_ordered = agg.set_index("stage").loc[order].reset_index()

    lower = (agg_ordered["median"] - agg_ordered["min"]).to_numpy(dtype=float)
    upper = (agg_ordered["max"] - agg_ordered["median"]).to_numpy(dtype=float)
    lower = np.where(np.isfinite(lower), lower, 0.0)
    upper = np.where(np.isfinite(upper), upper, 0.0)
    yerr = np.vstack([lower, upper])

    x_positions = np.arange(len(order))
    ax.errorbar(
        x=x_positions,
        y=agg_ordered["median"].to_numpy(dtype=float),
        yerr=yerr,
        fmt="none",
        capsize=5,
        linewidth=1.5,
        color="black",
        zorder=10,
    )

    ax.set_ylabel(y_label)
    ax.set_xlabel("Stage")
    ax.set_title(f"{indicator_name}: total by life cycle stage (median with min/max error bars)")
    plt.tight_layout()

    out_path = out_dir / OUTPUT_FILENAME
    fig.savefig(out_path, dpi=DPI)
    plt.close(fig)

# --------------------------------
# ENTITY EMISSIONS
# --------------------------------
def entity_emissions(csv_path: str | Path, output_dir: str | Path) -> None:
    """
    Create a circular (polar) bar plot of summed median Total net impact per element_eid,
    colored by entity, with element EID labels at bar tips.

    Args:
      csv_path: Input CSV path (expects columns including indicator_name, indicator_unit,
                element_eid, entity, total_net_impact_median)
      output_dir: Directory to write output PNG

    Returns:
      Path to the written PNG.
    """

    # ---- constants (frozen config) ----
    OUTPUT_FILENAME = "entity_emissions.png"
    ENTITY_GAP_BARS = 2
    SHOW_LEGEND = True
    CLIP_MIN = None
    CLIP_MAX = None
    LABEL_PAD_FRAC = 0.04
    FIGSIZE = (12, 12)
    DPI = 250

    csv_path = Path(csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / OUTPUT_FILENAME

    # ---- Load + clean ----
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip().str.lower()

    # Required columns (after lowercasing)
    required = {"indicator_name", "indicator_unit", "element_eid", "entity", "total_net_impact_median"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in CSV: {sorted(missing)}")

    emission_name = str(df["indicator_name"].dropna().iloc[0]) if df["indicator_name"].notna().any() else "Indicator"
    unit = str(df["indicator_unit"].dropna().iloc[0]) if df["indicator_unit"].notna().any() else ""

    df["total_net_impact_median"] = pd.to_numeric(df["total_net_impact_median"], errors="coerce")
    df = df.dropna(subset=["element_eid", "entity", "total_net_impact_median"]).copy()
    if df.empty:
        raise ValueError("No plottable rows after dropping NaNs in element_eid/entity/total_net_impact_median.")

    # ---- Aggregate ----
    agg = (
        df.groupby(["element_eid", "entity"], as_index=False)["total_net_impact_median"]
        .sum()
        .rename(columns={"total_net_impact_median": "impact"})
    )

    # If element_eid appears with multiple entities, keep the entity with largest |impact|
    if agg["element_eid"].duplicated().any():
        agg["abs_impact"] = agg["impact"].abs()
        agg = (
            agg.sort_values(["element_eid", "abs_impact"], ascending=[True, False])
            .drop_duplicates("element_eid", keep="first")
            .drop(columns=["abs_impact"])
        )

    if CLIP_MIN is not None or CLIP_MAX is not None:
        agg["impact"] = agg["impact"].clip(lower=CLIP_MIN, upper=CLIP_MAX)

    # ---- Order entities by total impact ----
    entity_totals = agg.groupby("entity")["impact"].sum().sort_values(ascending=False)
    entity_order = entity_totals.index.tolist()
    agg["entity"] = pd.Categorical(agg["entity"], categories=entity_order, ordered=True)
    agg = agg.sort_values(["entity", "impact"], ascending=[True, False]).reset_index(drop=True)

    entities = agg["entity"].astype(str).tolist()
    values = agg["impact"].to_numpy(dtype=float)

    # element_eid labels: try int, fall back to string
    eids = pd.to_numeric(agg["element_eid"], errors="coerce")
    eid_labels = np.where(eids.notna(), eids.astype(int).astype(str), agg["element_eid"].astype(str).to_numpy())

    # ---- Angular layout ----
    unique_entities = list(pd.unique(agg["entity"].astype(str)))
    counts = agg.groupby(agg["entity"].astype(str)).size().reindex(unique_entities).to_list()

    total_slots = int(sum(counts) + ENTITY_GAP_BARS * (len(unique_entities) - 1))
    if total_slots <= 0:
        raise ValueError("No slots to plot (empty aggregation).")

    slot_angles = np.linspace(0, 2 * np.pi, total_slots, endpoint=False)

    angles = np.zeros(len(agg), dtype=float)
    slot_idx = 0
    row_idx = 0

    for c in counts:
        angles[row_idx : row_idx + c] = slot_angles[slot_idx : slot_idx + c]
        slot_idx += c
        row_idx += c
        slot_idx += ENTITY_GAP_BARS

    slot_step = (2 * np.pi) / total_slots
    width = slot_step * 0.95

    # ---- Colors ----
    K = len(unique_entities)
    cmap = matplotlib.colormaps.get_cmap("tab20" if K <= 20 else "nipy_spectral")
    entity_to_color = {ent: cmap(i / max(K, 1)) for i, ent in enumerate(unique_entities)}
    colors = [entity_to_color[e] for e in entities]

    # ---- Plot ----
    fig = plt.figure(figsize=FIGSIZE)
    ax = plt.subplot(111, polar=True)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.bar(angles, values, width=width, color=colors, edgecolor="none")

    ax.set_xticks([])
    ax.grid(True, alpha=0.25)

    # ---- Add EID labels at bar tips (radial-aligned in screen space) ----
    max_abs = float(np.nanmax(np.abs(values))) if len(values) else 1.0
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    pad = max_abs * LABEL_PAD_FRAC

    def radial_screen_rotation_deg(theta: float, r0: float = 1.0, dr: float = 0.01) -> float:
        x0, y0 = ax.transData.transform((theta, r0))
        x1, y1 = ax.transData.transform((theta, r0 + dr))
        return float(np.degrees(np.arctan2(y1 - y0, x1 - x0)))

    for ang, v, eid in zip(angles, values, eid_labels):
        r = v + pad if v >= 0 else v - pad

        rot = radial_screen_rotation_deg(float(ang))
        rot += 180  # outside -> inside direction
        if 90 < (rot % 360) < 270:
            rot += 180

        ax.text(
            float(ang),
            float(r),
            str(eid),
            fontsize=4,
            rotation=rot,
            rotation_mode="anchor",
            ha="center",
            va="center",
        )

    # ---- Format radial ticks with unit ----
    def radial_formatter(x: float, pos: int) -> str:
        if unit:
            return f"{int(x):,} {unit}"
        return f"{int(x):,}"

    ax.yaxis.set_major_formatter(FuncFormatter(radial_formatter))
    ax.tick_params(axis="y", labelsize=7, colors="red")

    # ---- Legend ----
    if SHOW_LEGEND and K <= 30:
        handles = [Patch(facecolor=entity_to_color[e], label=e) for e in unique_entities]
        ax.legend(
            handles=handles,
            loc="center left",
            bbox_to_anchor=(1.05, 0.5),
            frameon=False,
            title="Entity",
        )

    # ---- Title ----
    ax.set_title(f"Median {emission_name} per element / entity", pad=20)

    plt.tight_layout()
    plt.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)

# --------------------------------
# COMBINED FUNCTION
# --------------------------------    

def _find_single_csv(dir_path: Path, prefix: str) -> Path | None:
    matches = sorted(dir_path.glob(f"{prefix}*.csv"))
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError(f"Multiple CSVs found in {dir_path} starting with '{prefix}': {matches}")
    return matches[0]

def create_plots(input_dir: str | Path) -> Path:
    input_path = Path(input_dir).expanduser().resolve()
    out_dir = input_path / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, str, Callable[[Path, Path], None]]] = [
        ("top25",  "object_type_summary_dissected_", top25_impacts),
        ("total",  "all_summary_dissected_",         total_emissions),
        ("entity", "all_summary_elements_",          entity_emissions),
    ]

    any_ran = False
    for name, prefix, fn in jobs:
        csv_path = _find_single_csv(input_path, prefix)
        if csv_path is None:
            print(f"⚠️  Skipping {name} plot: no CSV starting with '{prefix}' in {input_path}")
            continue
        fn(csv_path, out_dir)
        any_ran = True

    if not any_ran:
        print(f"⚠️  No plots generated in {out_dir} (no matching CSV inputs).")

    return out_dir


# --------------------------------
# SANKEY PLOT
# --------------------------------


def sankey_classification(csv_path: str | Path, output_dir: str | Path) -> None:

    # ---- frozen config ----
    OUTPUT_FILENAME = "ontology.png"
    PNG_SCALE = 2
    BACKGROUND_COLOR = "white"
    FONT_FAMILY = "Arial"
    FONT_SIZE = 9

    # ---- helpers ----
    def _norm_series(s: pd.Series, fallback: str) -> pd.Series:
        s = s.astype("string").str.strip().replace({"": pd.NA})
        return s.fillna(fallback)

    def _stable_color_from_key(key: str, alpha: float = 1.0) -> str:
        h = hashlib.sha256(key.encode("utf-8")).digest()
        hue = int.from_bytes(h[:2], "big") / 65535.0
        sat = 0.55 + (h[2] / 255.0) * 0.15
        lig = 0.45 + (h[3] / 255.0) * 0.10
        r, g, b = colorsys.hls_to_rgb(hue, lig, sat)
        R, G, B = int(r * 255), int(g * 255), int(b * 255)
        return f"rgba({R},{G},{B},{alpha})"

    def build_sankey_figure(df: pd.DataFrame) -> go.Figure:
        for col in ["entry_type", "material_type", "component_type", "facet_type"]:
            if col not in df.columns:
                df[col] = pd.NA

        df["entry_type"] = _norm_series(df["entry_type"], "unknown")
        df["material_type"] = _norm_series(df["material_type"], "unknown")
        df["component_type"] = _norm_series(df["component_type"], "unknown")
        df["facet_type"] = _norm_series(df["facet_type"], "unknown")

        # ---------- Layer 0: Root ----------
        df["root_label"] = "All"
        df["root_key"] = "root::All"

        # ---------- Layer 1: entry_type ----------
        entry_val = df["entry_type"].str.lower()
        df["entry_label"] = entry_val
        df["entry_key"] = "entry::" + entry_val

        # ---------- Layer 2: mid node ----------
        is_material = entry_val.eq("material")
        is_component = entry_val.eq("component")

        mid_label = pd.Series(pd.NA, index=df.index, dtype="string")
        mid_label.loc[is_material] = df.loc[is_material, "material_type"]
        mid_label.loc[is_component] = df.loc[is_component, "component_type"]
        mid_label = mid_label.fillna("other")
        df["mid_label"] = mid_label

        mid_key = pd.Series("mid::other::other", index=df.index, dtype="string")
        mid_key.loc[is_material] = "mid::material::" + df.loc[is_material, "material_type"]
        mid_key.loc[is_component] = "mid::component::" + df.loc[is_component, "component_type"]
        df["mid_key"] = mid_key

        # ---------- Layer 3: facet_type ----------
        facet_val = df["facet_type"].str.lower()
        is_unknown_facet = facet_val.eq("unknown")

        # display labels (can repeat "unknown")
        df["facet_label"] = df["facet_type"]
        df.loc[is_unknown_facet, "facet_label"] = "unknown"

        # node identity keys (avoid merging unknown facets across different mid nodes)
        df["facet_key"] = "facet::" + df["facet_type"]
        df.loc[is_unknown_facet, "facet_key"] = "facet::unknown_by_mid::" + df.loc[is_unknown_facet, "mid_key"]

        # ---------- Counts per node (for label "(n)") ----------
        root_counts = df.groupby("root_key").size().to_dict()
        entry_counts = df.groupby("entry_key").size().to_dict()
        mid_counts = df.groupby("mid_key").size().to_dict()
        facet_counts = df.groupby("facet_key").size().to_dict()

        def count_for_key(k: str) -> int:
            if k.startswith("root::"):
                return int(root_counts.get(k, 0))
            if k.startswith("entry::"):
                return int(entry_counts.get(k, 0))
            if k.startswith("mid::"):
                return int(mid_counts.get(k, 0))
            if k.startswith("facet::"):
                return int(facet_counts.get(k, 0))
            return 0

        # ---------- Aggregate link counts ----------
        hop0 = (
            df.groupby(["root_key", "root_label", "entry_key", "entry_label"], dropna=False)
            .size()
            .reset_index(name="count")
        )
        hop1 = (
            df.groupby(["entry_key", "entry_label", "mid_key", "mid_label"], dropna=False)
            .size()
            .reset_index(name="count")
        )
        hop2 = (
            df.groupby(["mid_key", "mid_label", "facet_key", "facet_label"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # ---------- Build ordered node list (keys + base labels) ----------
        def _collect_nodes(parts: list[tuple[pd.Series, pd.Series]]) -> list[tuple[str, str]]:
            seen = set()
            out: list[tuple[str, str]] = []
            for key_s, label_s in parts:
                for k, lab in zip(key_s.tolist(), label_s.tolist()):
                    if k not in seen:
                        seen.add(k)
                        out.append((k, lab))
            return out

        node_pairs = _collect_nodes(
            [
                (hop0["root_key"], hop0["root_label"]),
                (hop0["entry_key"], hop0["entry_label"]),
                (hop1["mid_key"], hop1["mid_label"]),
                (hop2["facet_key"], hop2["facet_label"]),
            ]
        )

        node_keys = [k for k, _ in node_pairs]
        base_labels = [lab for _, lab in node_pairs]
        node_labels = [f"{lab} ({count_for_key(k)})" for k, lab in zip(node_keys, base_labels)]

        node_id = {k: i for i, k in enumerate(node_keys)}
        node_colors = [_stable_color_from_key(k, alpha=0.95) for k in node_keys]

        # ---------- Links ----------
        sources: list[int] = []
        targets: list[int] = []
        values: list[int] = []
        link_colors: list[str] = []

        def link_color_from_source(source_key: str) -> str:
            return _stable_color_from_key(source_key, alpha=0.35)

        for _, r in hop0.iterrows():
            sources.append(node_id[r["root_key"]])
            targets.append(node_id[r["entry_key"]])
            values.append(int(r["count"]))
            link_colors.append(link_color_from_source(r["root_key"]))

        for _, r in hop1.iterrows():
            sources.append(node_id[r["entry_key"]])
            targets.append(node_id[r["mid_key"]])
            values.append(int(r["count"]))
            link_colors.append(link_color_from_source(r["entry_key"]))

        for _, r in hop2.iterrows():
            sources.append(node_id[r["mid_key"]])
            targets.append(node_id[r["facet_key"]])
            values.append(int(r["count"]))
            link_colors.append(link_color_from_source(r["mid_key"]))

        fig = go.Figure(
            data=[
                go.Sankey(
                    arrangement="snap",
                    node=dict(
                        label=node_labels,
                        pad=18,
                        thickness=16,
                        color=node_colors,
                        line=dict(width=0.5, color="rgba(0,0,0,0.25)"),
                    ),
                    link=dict(
                        source=sources,
                        target=targets,
                        value=values,
                        color=link_colors,
                    ),
                )
            ]
        )

        fig.update_layout(
            title="Sankey diagram classification (elements & layers)",
            paper_bgcolor=BACKGROUND_COLOR,
            plot_bgcolor=BACKGROUND_COLOR,
            font=dict(family=FONT_FAMILY, size=FONT_SIZE, color="black"),
            margin=dict(l=20, r=20, t=60, b=20),
        )
        return fig

    # ---- IO ----
    input_path = Path(csv_path).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"CSV not found: {input_path}")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / OUTPUT_FILENAME

    df = pd.read_csv(input_path)
    fig = build_sankey_figure(df)
    fig.write_image(str(out_path), scale=PNG_SCALE)