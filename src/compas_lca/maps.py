
from compas_lca.enums import MaterialType

from compas_lca.llm.ctx.material_context  import MINERAL_CTX
from compas_lca.llm.ctx.material_context  import CONCRETE_CTX
from compas_lca.llm.ctx.material_context  import LIGNEOUS_CTX
from compas_lca.llm.ctx.material_context  import METALLIC_CTX
from compas_lca.llm.ctx.material_context  import POLYMERIC_CTX
from compas_lca.llm.ctx.material_context  import BITUMINOUS_CTX
from compas_lca.llm.ctx.material_context  import COMPOSITE_CTX

from compas_lca.material.bituminous import BituminousFacet
from compas_lca.material.concrete import ConcreteFacet
from compas_lca.material.ligneous import LigneousFacet
from compas_lca.material.metallic import MetallicFacet
from compas_lca.material.mineral import MineralFacet
from compas_lca.material.polymeric import PolymericFacet
from compas_lca.material.composite import CompositeFacet

# Map material type facet context and facet model
CTX_BY_TYPE = {
    MaterialType.mineral: MINERAL_CTX,
    MaterialType.concrete: CONCRETE_CTX,
    MaterialType.ligneous: LIGNEOUS_CTX,
    MaterialType.metallic: METALLIC_CTX,
    MaterialType.polymeric: POLYMERIC_CTX,
    MaterialType.bituminous: BITUMINOUS_CTX,
    MaterialType.composite: COMPOSITE_CTX,
}

# Map material type facet context and facet model
MODEL_BY_TYPE = {
    MaterialType.mineral: MineralFacet,
    MaterialType.concrete: ConcreteFacet,
    MaterialType.ligneous: LigneousFacet,
    MaterialType.metallic: MetallicFacet,
    MaterialType.polymeric: PolymericFacet,
    MaterialType.bituminous: BituminousFacet,
    MaterialType.composite: CompositeFacet,
}
