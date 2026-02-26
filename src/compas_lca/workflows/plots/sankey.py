from pathlib import Path
import hashlib
import colorsys

import pandas as pd
import plotly.graph_objects as go


# =========================
# USER CONFIG (edit these)
# =========================
INPUT_CSV = r"temp/projects/duplex/06_report/GWPtotal/all_summary_dissected_GWPtotal.csv"
OUTPUT_PNG = r"temp/projects/duplex/06_report/GWPtotal/sankey.png"

PNG_SCALE = 2
BACKGROUND_COLOR = "white"
FONT_FAMILY = "Arial"
FONT_SIZE = 9  # small text
# =========================


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

    # Add counts in brackets next to each label
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
                    label=node_labels,  # label + (count)
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


def main() -> None:
    input_path = Path(INPUT_CSV).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"INPUT_CSV not found: {input_path}")

    out_path = Path(OUTPUT_PNG).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    fig = build_sankey_figure(df)
    fig.write_image(str(out_path), scale=PNG_SCALE)

    print(f"Wrote PNG to: {out_path}")


if __name__ == "__main__":
    main()