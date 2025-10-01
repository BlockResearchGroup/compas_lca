from enum import Enum

"""Enums for various categorical fields used in the extraction BaseModel classes."""

class YesNoUnknown(str, Enum):
    yes = "yes"
    no = "no"
    unknown = "unknown"

class YesNoEither(str, Enum):
    yes = "yes"
    no = "no"
    either = "either"
    unknown = "unknown"

class InteriorExterior(str, Enum):
    interior = "interior"
    exterior = "exterior"
    unknown = "unknown"

class DataResolution(str, Enum):
    generic = "generic"
    category_specific = "category_specific"    
    industry_specific = "industry_specific"      
    product_specific = "product_specific"        
    site_specific = "site_specific"              

class PureComposite(str, Enum):
    pure = "pure"
    composite = "composite"
    unknown = "unknown"

class FractionBasis(str, Enum):
    mass = "mass"
    volume = "volume"
    unknown = "unknown"

class LabelOrigin(str, Enum):
    literal="literal"
    canonical="canonical"

# this is uncertain
class MaterialRole(str, Enum):
    rebar="rebar"
    studs="studs"
    sheating="sheathing"
    grating="grating"
    loose_insulation="loose_insulation"
    rigid_insulation="rigid_insulation"
    air="air"
    gypsum_board="gypsum_board"
    concrete_matrix="concrete_matrix"
    adhesive="adhesive"
    fasteners="fasteners"
    other="other"
    unknown="unknown"