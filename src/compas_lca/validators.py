import re

from math import isfinite

from typing import Annotated
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

from pydantic import BeforeValidator

from compas_lca.enums import MaterialType
from compas_lca.enums import QuantUnit
from compas_lca.enums import QuantName
from compas_lca.enums import RefUnit
from compas_lca.enums import Loadbearing
from compas_lca.enums import InteriorExterior

Number = Union[int, float]

# -----------------------------------------------------------------------
# Material Type Validators (very exhaustive validator, due to importance)
# -----------------------------------------------------------------------

_WORD = re.compile(r"[a-z0-9]+")

def _norm_tokens(v: Any):
    """
    Lowercase; keep alnum; split to tokens; also provide the joined string for substring checks.
    """
    s = str(v).lower()
    tokens = _WORD.findall(s)
    joined = " ".join(tokens)
    return s, tokens, joined

def _has_any(joined: str, *phrases: str) -> bool:
    j = joined
    return any(p in j for p in phrases)

def _to_material_type(v: Any):
    """
    Normalize flexible inputs into MaterialType with careful precedence:
      1) explicit 'concrete' family (AAC, UHPC, RC, etc.)
      2) 'insulation' (incl. EPS/XPS/PIR/PUR/rockwool/cellulose, VIP, aerogel)
      3) bituminous (asphalt/bitumen/tar; catches 'asphalt concrete')
      4) metallic (steel/aluminum/copper/… incl. alloys)
      5) composite (FRP, sandwich, fiber-cement, GRC/GFRC, ACM)
      6) wood (wood/timber-based incl. CLT, LVL, glulam, OSB, MDF, bamboo, cork)
      7) polymeric (plastics/rubbers/resins not already mapped to insulation)
      8) mineral (ceramic/stone/glass/gypsum/cement/mortar/brick)
      → else unknown
    """
    try:
        MaterialType
    except NameError:
        return v

    if v is None:
        return MaterialType.unknown
    if isinstance(v, MaterialType):
        return v

    s, tokens, joined = _norm_tokens(v)
    tok = set(tokens)

    if (
        _has_any(joined,
                 "concrete", "reinforced concrete", "rc", "rcc",
                 "precast", "prestressed", "uhpc", "uhpfrc",
                 "shotcrete", "grout", "aac", "autoclaved aerated concrete",
                 "lightweight concrete", "sfrc", "fiber reinforced concrete")
        or ("aac" in tok) or ("rc" in tok) or ("uhpc" in tok) or ("uhpfrc" in tok)
        or (_has_any(joined, "cementitious screed") and "concrete" in joined)
    ) and not _has_any(joined, "asphalt concrete"):  # asphalt-concrete is bituminous
        return MaterialType.concrete
    if (
        _has_any(joined, "asphalt", "bitumen", "bituminous", "tar", "pitch",
                 "mastic asphalt", "modified bitumen", "sbs", "app",
                 "roofing felt", "asphalt concrete")
        or "bitumen" in tok or "asphalt" in tok
    ):
        return MaterialType.bituminous
    if any(m in tok for m in [
        "metal", "metallic", "steel", "stainless", "inox", "aluminum", "aluminium",
        "copper", "brass", "bronze", "zinc", "titanium", "iron", "cast", "galvanized"
    ]):
        return MaterialType.metallic
    if (
        "composite" in tok
        or _has_any(joined, "frp", "cfrp", "gfrp", "kfrp", "aramid",
                    "carbon fiber", "glass fiber", "fiberglass",
                    "fiber reinforced", "fibre reinforced",
                    "sandwich panel", "honeycomb core",
                    "aluminum composite material", "acm",
                    "fiber cement", "fibre cement",
                    "grc", "gfrc")
        or "acm" in tok or "frp" in tok or "cfrp" in tok or "gfrp" in tok
        or "gfrc" in tok or "grc" in tok
    ):
        return MaterialType.composite
    if (
        _has_any(
            joined,
            "wood", "timber", "lumber", "hardwood", "softwood",
            "parquet",
            "plywood", "osb", "mdf", "hdf", "particleboard", "chipboard",
            "fiberboard", "fibreboard", "hardboard",
            "glulam", "glued laminated", "lvl", "psl", "kvh",
            "clt", "cross laminated timber",
            "veneer", "lamella", "straw", "bamboo", "cork",
            "wood fibre", "wood fiber", "woodfibre"
        )
        or any(x in tok for x in ["wood", "timber", "plywood", "osb", "mdf", "clt", "lvl", "psl", "kvh"])
    ):
        return MaterialType.wood
    if (
        "polymer" in tok or "polymeric" in tok or "plastic" in tok
        or _has_any(joined, "rubber", "resin", "silicone", "epoxy", "acrylic",
                    "polyester", "vinyl")
        or any(abbr in tok for abbr in [
            "pvc", "pe", "hdpe", "ldpe", "pp", "pet", "pbt", "pc",
            "pmma", "abs", "hips", "ptfe", "pfa", "peek", "pu", "xps", "eps"
        ])
    ):
        return MaterialType.polymeric
    if (
        _has_any(joined, "mineral", "ceramic", "porcelain", "tile", "brick", "masonry",
                 "stone", "marble", "granite", "limestone", "sandstone", "slate",
                 "terra cotta", "terracotta",
                 "glass", "glass ceramic", "quartz",
                 "gypsum", "plaster", "anhydrite", "cement", "mortar",
                 "lime", "perlite", "vermiculite")
    ):
        return MaterialType.mineral
    if (
        _has_any(joined,
                 "cotton",
                 "flax", "linen",
                 "hemp",
                 "sheep wool", "wool", "alpaca", "camel hair", "llama wool",
                 "straw", "hay",
                 "jute", "kenaf", "sisal",
                 "coir", "coconut fiber", "coconut fibre", "coir fiber", "coir fibre",
                 "miscanthus",
                 "reed", "phragmites", "cattail", "typha",
                 "rice husk", "ricehusk", "husk", "hulls", "hull",
                 "rice hull", "olive pits", "nut shell", "nut shells",
                 "bio-based binder", "starch binder", "casein", "natural latex", "rubber (natural)")
        or any(x in tok for x in [
            "cotton", "flax", "linen", "hemp", "wool", "alpaca", "camel", "llama",
            "straw", "jute", "kenaf", "sisal", "coir", "miscanthus",
            "reed", "typha", "husk", "hulls", "hull",
        ])
    ) and not _has_any(joined, "wood", "timber", "mdf", "hdf", "osb", "particleboard",
                       "plywood", "clt", "glulam", "lvl", "bamboo board", "woodfibre"):
        return MaterialType.biobased

    return MaterialType.unknown

# -------------------------------------------------------------------------------
# Validator for Reference Units (such that any database/epd can be standardized)
# -------------------------------------------------------------------------------


def _norm_tokens(v: Any):
    """Lowercase; keep alnum; split to tokens; also provide the joined string."""
    s = str(v).strip().lower()
    tokens = _WORD.findall(s)
    joined = " ".join(tokens)
    return s, tokens, joined

def _has_any(joined: str, *phrases: str) -> bool:
    j = joined
    return any(p in j for p in phrases)

def _to_ref_unit(v: Any):
    """
    Normalize flexible inputs into RefUnit:
      - 'sqm', 'qm', 'm^2', 'm²' → m2
      - 'cbm', 'm^3', 'm³'       → m3
      - 'lm', 'lfm', 'laufmeter' → m
      - 'pc', 'pcs', 'stück'     → pcs
      - 'kg', 'kilogram(s)'      → kg

    Rules:
      - If multiple units are detected in the same string (e.g. 'kg per m2'), raise ValueError.
      - If nothing matches, raise ValueError.
    """
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError("reference unit is required")
    if isinstance(v, RefUnit):
        return v

    s, tokens, joined = _norm_tokens(v)
    if re.search(r"\b(ft|feet|inch|in|yard|yd|mile|mi|ft2|ft\^?2|ft²|ft3|ft\^?3|ft³)\b", joined):
        raise ValueError(f"non-SI unit detected in {v!r}; please convert to SI (kg, m, m2, m3, pcs)")
    tok = set(tokens)

    # Compact matchers (cover unicode and caret exponents)
    m2_hit = (
        bool(re.search(r"\bm\s*(?:\^?\s*2|[²\u00b2])\b", joined))
        or any(t in tok for t in {"m2", "m^2", "m²", "sqm", "qm"})
        or _has_any(joined, "square meter", "square metre", "sq m", "sq. m")
    )
    m3_hit = (
        bool(re.search(r"\bm\s*(?:\^?\s*3|[³\u00b3])\b", joined))
        or any(t in tok for t in {"m3", "m^3", "m³", "cbm"})
        or _has_any(joined, "cubic meter", "cubic metre", "cu m", "kubikmeter")
    )
    m_hit = (
        ("m" in tok)
        or any(t in tok for t in {"lm", "lfm", "lfdm"})
        or _has_any(joined, "linear meter", "linear metre", "laufmeter")
    )
    kg_hit = (
        ("kg" in tok)
        or any(t in tok for t in {"kgs", "kilogram", "kilograms", "kilogramme", "kilogrammes"})
    )
    pcs_hit = any(t in tok for t in {
        "pcs","pc","piece","pieces","unit","units","ea","each","stk","stck","stueck","stück"
    })

    hits = []
    if m2_hit: hits.append(RefUnit.m2)
    if m3_hit: hits.append(RefUnit.m3)
    if m_hit:  hits.append(RefUnit.m)
    if kg_hit: hits.append(RefUnit.kg)
    if pcs_hit: hits.append(RefUnit.pcs)

    # Fallback: exact single-token strings like "m²"
    if not hits:
        single = s.replace(" ", "")
        if single in {"m²", "m^2"}: return RefUnit.m2
        if single in {"m³", "m^3"}: return RefUnit.m3

    # De-dup and decide
    dedup = []
    for h in hits:
        if h not in dedup:
            dedup.append(h)

    if not dedup:
        raise ValueError(f"could not infer reference unit from {v!r}")
    if len(dedup) > 1:
        raise ValueError(f"ambiguous reference unit in {v!r}: candidates {', '.join(u.value for u in dedup)}")
    return dedup[0]


# -------------------------------------------------------------------------------
# Validator to standardized quantity values (m,m2,m3)
# -------------------------------------------------------------------------------

# Common SI prefixes for AEC workflows (symbols + names)
# Factors are for LENGTH; raise to power 2/3 for area/volume.
_SI_PREFIX = {
    # symbols
    "µ": 1e-6, "μ": 1e-6, "u": 1e-6,  # micrometre (ASCII 'u' accepted)
    "m": 1e-3,                        # millimetre
    "c": 1e-2,                        # centimetre
    "d": 1e-1,                        # decimetre
    "k": 1e+3,                        # kilometre

    # names (IFC / prose)
    "micro": 1e-6,
    "milli": 1e-3,
    "centi": 1e-2,
    "deci":  1e-1,
    "kilo":  1e+3,
}

def _unit_info(s: Any) -> Tuple[QuantUnit, float, int]:
    """
    Returns (canonical_unit, factor_to_canonical, power),
    where power=1(length), 2(area), 3(volume).
    Raises ValueError if not interpretable as metre-based unit.
    """
    if s is None or (isinstance(s, str) and not s.strip()):
        raise ValueError("unit is required")
    if isinstance(s, QuantUnit):
        return s, 1.0, {QuantUnit.m:1, QuantUnit.m2:2, QuantUnit.m3:3}[s]

    raw = str(s).strip()
    joined = re.sub(r"\s+", " ", raw).lower()

    power = 1
    if any(w in joined for w in ["square ", " sq ", "sq.", "quadratic "]): power = 2
    if "cubic " in joined: power = 3
    if re.search(r"\b\^?\s*2\b|[²\u00b2]", joined): power = 2
    if re.search(r"\b\^?\s*3\b|[³\u00b3]", joined): power = 3
    if joined.startswith(("square_", "square")): power = 2
    if joined.startswith(("cubic_", "cubic")): power = 3

    # IFC names (with/without underscore): e.g. SQUARE_CENTIMETRE, CUBICMILLIMETRE, MILLIMETRE, METRE
    m_ifc = re.match(r"^(?:square_?|cubic_?)?(micro|milli|centi|deci|kilo)?metre$", joined)
    if m_ifc:
        pf = _SI_PREFIX.get(m_ifc.group(1), 1.0)
        unit = QuantUnit.m if power == 1 else (QuantUnit.m2 if power == 2 else QuantUnit.m3)
        return unit, (pf ** power), power

    # “square meter”, “cubic metre”, etc.
    if re.search(r"\bmetre(s)?\b|\bmeter(s)?\b", joined):
        unit = QuantUnit.m if power == 1 else (QuantUnit.m2 if power == 2 else QuantUnit.m3)
        m_word = re.search(r"(micro|milli|centi|deci|kilo)\s+metre?", joined)
        pf = _SI_PREFIX[m_word.group(1)] if m_word else 1.0
        return unit, (pf ** power), power

    # Symbolic: m, mm, cm2, mm^2, m²/m³, mm2/cm3
    token = joined.replace(" ", "").replace("linear", "")
    if token.endswith(("^2", "²", "2")): power, token = 2, token[:-2] if token.endswith("^2") else token[:-1]
    if token.endswith(("^3", "³", "3")): power, token = 3, token[:-2] if token.endswith("^3") else token[:-1]

    if token == "m":
        unit = QuantUnit.m if power == 1 else (QuantUnit.m2 if power == 2 else QuantUnit.m3)
        return unit, 1.0, power

    if re.fullmatch(r"(?:µ|μ|u|m|c|d|k)?m", token):
        prefix_symbol = token[:-1]
        pf = _SI_PREFIX.get(prefix_symbol, 1.0)
        unit = QuantUnit.m if power == 1 else (QuantUnit.m2 if power == 2 else QuantUnit.m3)
        return unit, (pf ** power), power

    raise ValueError(f"could not interpret unit {raw!r} as metres/metres²/metres³")


def _unit_scale_to_m(s: Any) -> Tuple[QuantUnit, float]:
    u, k, _ = _unit_info(s)
    return u, k

# --- the validator expected by Pydantic Annotated ---
def _to_quant_unit(v: Any) -> QuantUnit:
    """Normalize any metre/area/volume expression (incl. IFC) to QuantUnit m/m2/m3 (ignores scale)."""
    unit, _ = _unit_scale_to_m(v)
    return unit

# maps common aliases/fields → QuantName
_ALIAS_TO_QUANT = {
    # thickness
    "thickness": QuantName.thickness,
    "core thickness": QuantName.thickness,
    "dicke": QuantName.thickness, "dicken": QuantName.thickness,
    # area
    "area": QuantName.area, "fläche": QuantName.area, "flaeche": QuantName.area,
    "surface": QuantName.area, "surface_area": QuantName.area,
    "net_area": QuantName.area, "gross_area": QuantName.area,
    "net_side_area": QuantName.area, "net_surface_area": QuantName.area,
    # volume
    "volume": QuantName.volume, "vol": QuantName.volume,
    "net_volume": QuantName.volume, "gross_volume": QuantName.volume,
    # length
    "length": QuantName.length, "len": QuantName.length, "span": QuantName.length,
    "laufmeter": QuantName.length, "linear": QuantName.length,
    "width": QuantName.length, "height": QuantName.length, "depth": QuantName.length,
}

def _to_quant_name(v: Any) -> QuantName:
    """
    Normalize flexible inputs (names, aliases, units) into QuantName.

    Rules:
      - If `v` already QuantName → return.
      - If name/alias contains 'thick' → thickness.
      - Else if name/alias matches known area/volume/length keys → that class.
      - Else if `v` looks like a unit (e.g., 'mm²', 'CUBIC_MILLIMETRE'), infer by dimension:
            power 1 → length, 2 → area, 3 → volume.
      - Otherwise raise ValueError.
    """
    if isinstance(v, QuantName):
        return v
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError("quantity name is required")

    s = str(v).strip()
    joined = re.sub(r"\s+", " ", s).lower()

    # explicit ‘thick’ wins over unit-based inference (common for wall panels)
    if "thick" in joined:
        return QuantName.thickness

    # direct alias table (exact or token-ish matches)
    key = joined.replace(" ", "_")
    if key in _ALIAS_TO_QUANT:
        return _ALIAS_TO_QUANT[key]
    if joined in _ALIAS_TO_QUANT:
        return _ALIAS_TO_QUANT[joined]

    # try unit-based inference (reuses the unit parser)
    try:
        _, _, power = _unit_info(joined)
        if power == 3:
            return QuantName.volume
        if power == 2:
            return QuantName.area
        # power == 1 → default length (unless 'thick' already caught)
        return QuantName.length
    except ValueError:
        pass

    # last-chance keyword heuristics
    if any(w in joined for w in ["area", "fläche", "flaeche", "surface"]):
        return QuantName.area
    if any(w in joined for w in ["volume", "vol"]):
        return QuantName.volume
    if any(w in joined for w in ["length", "laufmeter", "linear", "span", "width", "height", "depth"]):
        return QuantName.length

    raise ValueError(f"could not infer quantity name from {v!r}")



# -------------------------------------------------------------------
# Core reusable validators (helpers)
# -------------------------------------------------------------------


def _parse_number(v: Any) -> Number:
    """
    Accept int/float directly; cast strings like "2", "2.5", "1e3" to int/float.
    """
    if v is Ellipsis or v == "":
        raise ValueError("value is required")
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    try:
        return float(s) if ("." in s or "e" in s.lower()) else int(s)
    except Exception as exc:
        raise ValueError(f"Cannot cast value {v!r} to number") from exc

def _finite_fraction(v: Any) -> float:
    """
    Accept numbers or numeric strings; ensure finite; clamp tiny epsilons
    into [0, 1] with 1e-9 tolerance (to mirror your old _finite_fraction).
    """
    if isinstance(v, str):
        v = float(v.strip() or "nan")
    if not isfinite(v):
        raise ValueError("fraction must be finite")
    if -1e-9 <= v < 0:
        return 0.0
    if 1 < v <= 1 + 1e-9:
        return 1.0
    return float(v)


def _to_loadbearing(v: Any):
    """
    Normalize loadbearing to YesNoEither, with a vocabulary tailored to structure.
    """
    # If enums are stubbed (tests), just return-through
    if Loadbearing is object:
        return v
    if v is None:
        return Loadbearing.unknown
    if isinstance(v, Loadbearing):
        return v
    s = str(v).strip().lower()
    if s in {"loadbearing","yes", "true", "y", "1", "structural", "load-bearing"}:
        return Loadbearing.loadbearing
    if s in {"non_loadbearing", "no", "false", "n", "0", "non-structural", "nonstructural", "non_load-bearing"}:
        return Loadbearing.non_loadbearing
    if s in {"either", "both", "variable", "depends", "sometimes", "mixed", "contextual", "maybe"}:
        return Loadbearing.either
    return None


def _to_inex(v: Any):
    """
    Normalize interior/exterior to YesNoEither, with location-centric vocabulary.
    """
    if InteriorExterior is object:
        return v
    if v is None:
        return InteriorExterior.unknown
    if isinstance(v, InteriorExterior):
        return v
    s = str(v).strip().lower()
    if s in {"interior", "yes", "true", "y", "1", "inside", "indoor"}:
        return InteriorExterior.interior
    if s in {"exterior", "no", "false", "n", "0", "outside", "outdoor", "façade", "facade"}:
        return InteriorExterior.exterior
    if s in {"either", "both", "variable", "mixed", "contextual"}:
        return InteriorExterior.either
    return None

# Accept common unit notations (various spellings)
_UNIT_PATTERN = re.compile(
    r"\s*(kg\s*/?\s*m\^?3|kg\s*per\s*m3|kg\s*/\s*m3|kg\s*/?\s*m³)\s*",
    flags=re.IGNORECASE,
)

def _normalize_density(v: Any) -> Optional[float]:
    """
    Normalize density values.
    Acceptable inputs:
      - Numbers: 2400, 1850.5
      - Strings with units: "2400 kg/m3", "1'850 kg/m³"
      - European decimals: "2,5", "1'850,75"
    Rules:
      - Apostrophe (') → thousands separator → remove
      - Comma (,) → decimal separator → replace with dot
      - Remove units and whitespace
      - Return float or None if parsing fails
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower()
    if not s:
        return None
    s = s.replace("'", "") # Remove thousands separators
    s = s.replace(",", ".") # Replace European decimal comma with dot
    s = s.replace(" ", "") # Remove spaces
    s = _UNIT_PATTERN.sub("", s) # Remove common unit suffixes
    try:
        return float(s)
    except ValueError:
        return None

def _normalize_areal_density(v: Any) -> Optional[float]:
    """
    Normalize areal density values.
    Accepts numbers or strings like '12 kg/m2', '1.2 kg/m²', '1,200 g/m2'.
    Returns float in kg/m².
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower()
    if not s:
        return None
    s = s.replace("'", "").replace(",", ".").replace(" ", "")
    # Convert g/m² → kg/m²
    if "g/m2" in s or "g/m²" in s:
        s = re.sub(r"\s*g\s*/?\s*m[²2]", "", s)
        try:
            return float(s) / 1000.0
        except ValueError:
            return None
    # Handle kg/m² and variants
    s = re.sub(r"\s*kg\s*/?\s*m[²2]", "", s)
    try:
        return float(s)
    except ValueError:
        return None

def _normalize_thickness(v: Any) -> Optional[float]:
    """
    Normalize thickness values (in millimeters).
    Accepts:
    - numbers directly (int/float)
    - strings like "250", "250 mm", "2.5 cm", "0.25 m"
    - strips commas, spaces, and unit labels
    - returns float (always representing millimeters)
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower()
    if not s:
        return None
    s = s.replace(",", ".").replace(" ", "") # unify decimal separator
    factor = 1.0 # infer approximate unit multiplier
    if "cm" in s:
        factor = 10.0        # cm → mm
    elif "m" in s:
        factor = 1000.0      # m → mm
    # remove unit labels for parsing
    s = re.sub(r"(mm|millimet(er|re)s?|cm|centimet(er|re)s?|m|met(er|re)s?)", "", s)
    try:
        return float(s) * factor
    except ValueError:
        return None


def _parse_lambda_value(v: Any) -> Optional[float]:
    """
    Accept numbers or strings like '0.035', '0,035 W/mK', etc.
    Normalize commas, strip whitespace, and remove unit text.
    Return float or None.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower().replace(",", ".")
    # remove common unit notations like "W/mK", "W/m·K", "W / m K"
    s = re.sub(r"\s*w\s*/?\s*m\s*[·]?\s*k", "", s)
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return None


def _parse_u_value(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower().replace(",", ".")
    # remove common unit text (W/m²K, W/m2K, W/m^2K, etc.)
    s = re.sub(r"\s*w\s*/?\s*m[²2]\^?2k", "", s)
    s = re.sub(r"\s*w\s*/\s*m2k", "", s)
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return None

def _normalize_manufacturer(v: Any) -> Optional[str]:
    """
    Normalize manufacturer or brand strings:
    - Converts to stripped string (empty → None)
    - Removes trademark and service mark symbols (®, ™, ℠)
    - Removes surrounding whitespace
    - Passes through non-strings and None
    """
    if v is None:
        return None
    if not isinstance(v, str):
        return v
    s = v.strip()
    if not s:
        return None
    s = re.sub(r"[®™℠❖]", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = s.strip()
    return s or None


# -------------------------------------------------------------------
# Public Annotated field types
# -------------------------------------------------------------------

# Common pre-bound variants (handy in most models)
ManufacturerStr = Annotated[Optional[str], BeforeValidator(_normalize_manufacturer)]

ParsedNumber = Annotated[Number, BeforeValidator(_parse_number)]

# Domain-specific enums normalized from flexible inputs
LoadbearingType = Annotated[Loadbearing, BeforeValidator(_to_loadbearing)]
InteriorExteriorType  = Annotated[InteriorExterior, BeforeValidator(_to_inex)]
RefUnitType = Annotated[RefUnit, BeforeValidator(_to_ref_unit)]
QuantUnitType = Annotated[QuantUnit, BeforeValidator(_to_quant_unit)]
QuantNameType = Annotated[QuantName, BeforeValidator(_to_quant_name)]

# Normalized Floats (addressing potential unit inclusions)
DensityFloat = Annotated[Optional[float], BeforeValidator(_normalize_density)]
ArealDensityFloat = Annotated[Optional[float], BeforeValidator(_normalize_areal_density)]
UValueFloat = Annotated[Optional[float], BeforeValidator(_parse_u_value)]
LambdaFloat = Annotated[Optional[float], BeforeValidator(_parse_lambda_value)]
ThicknessFloat = Annotated[Optional[float], BeforeValidator(_normalize_thickness)]

# Clamps fractions (0..1) with 1e-9 tolerance
FiniteFraction = Annotated[float, BeforeValidator(_finite_fraction)]

# Public Annotated type
MaterialTypeValidated = Annotated[MaterialType, BeforeValidator(_to_material_type)]