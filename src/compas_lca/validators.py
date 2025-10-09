import re

from math import isfinite

from typing import Annotated
from typing import Any
from typing import Callable
from typing import Optional
from typing import Union

from pydantic import BeforeValidator

from compas_lca.enums import Loadbearing
from compas_lca.enums import DataResolution
from compas_lca.enums import InteriorExterior

Number = Union[int, float]

# -------------------------------------------------------------------
# Core reusable validators (helpers)
# -------------------------------------------------------------------

def _strip_string_or_none(v: Any) -> Optional[str]:
    """
    Convert strings to stripped strings; empty -> None.
    Pass-through for non-strings and None.
    """
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s or None
    return v


def _require_non_empty_str(field: str) -> Callable[[Any], str]:
    """
    Build a string validator that:
    - rejects Ellipsis or empty/whitespace strings
    - strips whitespace
    - uses a field-specific error message
    """
    def _validator(v: Any) -> str:
        if v is Ellipsis or v == "":
            raise ValueError(f"{field} is required")
        s = str(v).strip()
        if s == "":
            raise ValueError(f"{field} must not be empty")
        return s
    return _validator


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


def _to_data_resolution(v: Any):
    """
    Normalize free-text resolution strings to DataResolution levels.
    """
    if DataResolution is object:
        return v

    if v is None:
        return DataResolution.generic
    if isinstance(v, DataResolution):
        return v

    s = str(v).strip().lower()
    s = re.sub(r"[\s\-_]+", " ", s)

    if any(k in s for k in ["site specific", "single site", "plant", "production site", "factory"]):
        return DataResolution.site_specific
    if any(k in s for k in ["product specific", "manufacturer specific", "vendor specific", "brand"]):
        return DataResolution.product_specific
    if any(k in s for k in ["industry", "association", "sector", "collective", "consortium"]):
        return DataResolution.industry_specific
    if any(k in s for k in ["category", "market average", "national average", "regional average", "representative"]):
        return DataResolution.category_specific
    if any(k in s for k in ["generic", "template", "placeholder", "unspecific", "sample epd"]):
        return DataResolution.generic
    return DataResolution.generic


# Accept numbers and strings with optional 'kg/m3' / 'kg/m^3' / 'kg/m³' units and commas.
_UNIT_PATTERN = re.compile(
    r"\s*(kg\s*/?\s*m\^?3|kg\s*per\s*m3|kg\s*/\s*m3|kg/m³)\s*",
    flags=re.IGNORECASE,
)
def _normalize_density(v: Any) -> Optional[float]:
    """
    Normalize density values:
    - Accept numbers directly (int/float)
    - Accept strings with units like '2400 kg/m3', '1,200 kg/m³'
    - Strip commas, whitespace, and unit text
    - Return float or None
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower()
    if not s:
        return None
    # Remove thousands separators
    s = s.replace(",", "")
    # Remove unit labels (various spellings)
    s = _UNIT_PATTERN.sub("", s)

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
    # unify decimal separator
    s = s.replace(",", ".").replace(" ", "")
    # infer approximate unit multiplier
    factor = 1.0
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


# -------------------------------------------------------------------
# Public Annotated field types
# -------------------------------------------------------------------

# Common pre-bound variants (handy in most models)
NameStr = Annotated[str, BeforeValidator(_require_non_empty_str("name"))]
UnitStr = Annotated[str, BeforeValidator(_require_non_empty_str("unit"))]

ParsedNumber = Annotated[Number, BeforeValidator(_parse_number)]

# Optional string that is stripped; empty string -> None
StrippedStr = Annotated[Optional[str], BeforeValidator(_strip_string_or_none)]

# Domain-specific enums normalized from flexible inputs
LoadbearingType = Annotated["Loadbearing", BeforeValidator(_to_loadbearing)]
InteriorExteriorType  = Annotated["InteriorExterior", BeforeValidator(_to_inex)]
DataResolutionType = Annotated["DataResolution", BeforeValidator(_to_data_resolution)]

# Normalized Floats (addressing potential unit inclusions)
DensityFloat = Annotated[Optional[float], BeforeValidator(_normalize_density)]
UValueFloat = Annotated[Optional[float], BeforeValidator(_parse_u_value)]
LambdaFloat = Annotated[Optional[float], BeforeValidator(_parse_lambda_value)]
ThicknessFloat = Annotated[Optional[float], BeforeValidator(_normalize_thickness)]

# Clamps fractions (0..1) with 1e-9 tolerance
FiniteFraction = Annotated[float, BeforeValidator(_finite_fraction)]
