from typing import Optional
from typing import List

from compas_lca.matching_core.core import MatchingCore

from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.model.quantity import Quantities
from compas_lca.model.lca_element import LcaElement

from compas_lca.inventory.indicator import Indicators
from compas_lca.inventory.metadata import ItemMetadata
from compas_lca.inventory.item import InventoryItem
from compas_lca.inventory.reference import ReferenceInfo

def edit_lca_element(
        element: LcaElement,
        *,
        override_descriptor: Optional[ElementDescriptor] = None,
        override_element_core: Optional[List[MatchingCore]] = None,
        override_quantities: Optional[Quantities] = None,
) -> LcaElement:
    """
    Return a copy of an LcaElement with optional overrides applied (for editing).

    The `id` of the element is **always preserved**.  
    Only fields with non-None overrides are replaced.

    Parameters
    ----------
    element : LcaElement
        The existing InventoryItem instance to modify.
    override_descriptor : Optional[ElementDescriptor]
        Replacement for the element's descriptor field.
    override_element_core : Optional[List[MatchingCore]]
        Replacement for the elements's element_core
        (list of MatchingCore objects)
    override_quantities : Optional[Quantities]
        Replacement for the elements Quantities
        (list of Quantity objects)

    Returns
    -------
    LcaElement
        A new LcaElement instance with overrides applied, sharing the same ID.
    """
    updates = {}
    if override_descriptor is not None:
        updates["descriptor"] = override_descriptor
    if override_element_core is not None:
        updates["element_core"] = override_element_core
    if override_quantities is not None:
        updates["quantities"] = override_quantities

    # Use Pydantic model_copy to preserve id and validate updated fields
    patched = element.model_copy(update=updates)

    # Safety check — the ID must never change
    if patched.id != element.id:
        raise RuntimeError("edit_lca_element must not change the LcaElement id.")

    return patched



def edit_inventory_item(
    item: InventoryItem,
    *,
    override_matching_core: Optional[MatchingCore] = None,
    override_indicators: Optional[Indicators] = None,
    override_reference: Optional[ReferenceInfo] = None,
    override_metadata: Optional[ItemMetadata] = None,
) -> InventoryItem:
    """
    Return a copy of an InventoryItem with optional overrides applied (for editing).

    The `id` of the item is **always preserved**.  
    Only fields with non-None overrides are replaced.

    Parameters
    ----------
    item : InventoryItem
        The existing InventoryItem instance to modify.
    override_matching_core : MatchingCore, optional
        Replacement for the item's matching core data.
    override_indicators : Indicators, optional
        Replacement for the item's indicator data.
    override_reference : ReferenceInfo, optional
        Replacement for the item's reference data.
    override_metadata : EnvDataSource, optional
        Replacement for the item's data source.

    Returns
    -------
    InventoryItem
        A new InventoryItem instance with overrides applied, sharing the same ID.
    """
    updates = {}
    if override_matching_core is not None:
        updates["item_core"] = override_matching_core
    if override_indicators is not None:
        updates["indicators"] = override_indicators
    if override_reference is not None:
        updates["reference"] = override_reference
    if override_metadata is not None:
        updates["source"] = override_metadata

    # Use Pydantic model_copy to preserve id and validate updated fields
    patched = item.model_copy(update=updates)

    # Safety check — the ID must never change
    if patched.id != item.id:
        raise RuntimeError("edit_inventory_item must not change the InventoryItem id.")

    return patched
