import re

from math import isfinite

from typing import Annotated
from typing import Any
from typing import Optional
from typing import Union

from pydantic import BeforeValidator

from compas_lca.enums import MaterialType
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
      6) ligneous (wood/timber-based incl. CLT, LVL, glulam, OSB, MDF, bamboo, cork)
      7) polymeric (plastics/rubbers/resins not already mapped to insulation)
      8) mineral (ceramic/stone/glass/gypsum/cement/mortar/brick)
      → else unknown
    """
    # If enum is stubbed in tests
    try:
        MaterialType  # type: ignore[name-defined]
    except NameError:
        return v

    if v is None:
        return MaterialType.unknown
    if isinstance(v, MaterialType):
        return v

    s, tokens, joined = _norm_tokens(v)
    tok = set(tokens)

    # Concrete (explicit standalone class)
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

    # Bituminous
    if (
        _has_any(joined, "asphalt", "bitumen", "bituminous", "tar", "pitch",
                 "mastic asphalt", "modified bitumen", "sbs", "app",
                 "roofing felt", "asphalt concrete")
        or "bitumen" in tok or "asphalt" in tok
    ):
        return MaterialType.bituminous

    # Metallic
    if any(m in tok for m in [
        "metal", "metallic", "steel", "stainless", "inox", "aluminum", "aluminium",
        "copper", "brass", "bronze", "zinc", "titanium", "iron", "cast", "galvanized"
    ]):
        return MaterialType.metallic

    # Composite (wins over mineral/polymeric for specific phrases)
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

    # Ligneous (wood & plant-based)
    if (
        _has_any(joined, "wood", "timber", "lumber", "hardwood", "softwood",
                 "plywood", "osb", "mdf", "hdf", "particleboard", "chipboard",
                 "fiberboard", "glulam", "glued laminated", "lvl", "psl", "kvh",
                 "clt", "cross laminated timber", "veneer", "lamella", "straw"
                 "bamboo", "cork")
        or any(x in tok for x in ["wood", "timber", "plywood", "osb", "mdf", "clt", "lvl", "psl", "kvh"])
    ):
        return MaterialType.ligneous

    # Polymeric (plastics/rubbers/resins not already matched as insulation)
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

    # Mineral (ceramic/stone/glass/gypsum/cement/mortar/brick)
    if (
        _has_any(joined, "mineral", "ceramic", "porcelain", "tile", "brick", "masonry",
                 "stone", "marble", "granite", "limestone", "sandstone", "slate",
                 "terra cotta", "terracotta",
                 "glass", "glass ceramic", "quartz",
                 "gypsum", "plaster", "anhydrite", "cement", "mortar",
                 "lime", "perlite", "vermiculite")
    ):
        return MaterialType.mineral

    return MaterialType.unknown




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
    return Loadbearing.unknown


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
    return InteriorExterior.unknown

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
LoadbearingType = Annotated["Loadbearing", BeforeValidator(_to_loadbearing)]
InteriorExteriorType  = Annotated["InteriorExterior", BeforeValidator(_to_inex)]

# Normalized Floats (addressing potential unit inclusions)
DensityFloat = Annotated[Optional[float], BeforeValidator(_normalize_density)]
ArealDensityFloat = Annotated[Optional[float], BeforeValidator(_normalize_areal_density)]
UValueFloat = Annotated[Optional[float], BeforeValidator(_parse_u_value)]
LambdaFloat = Annotated[Optional[float], BeforeValidator(_parse_lambda_value)]
ThicknessFloat = Annotated[Optional[float], BeforeValidator(_normalize_thickness)]

# Clamps fractions (0..1) with 1e-9 tolerance
FiniteFraction = Annotated[float, BeforeValidator(_finite_fraction)]

# Public Annotated type
MaterialTypeValidated = Annotated["MaterialType", BeforeValidator(_to_material_type)]