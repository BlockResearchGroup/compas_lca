class Inventory:
    """An inventory of Life Cycle Assessment (LCA) items."""
    def __init__(self):
        self.items = []

    def from_excel(self, filepath: str):
        """Load an inventory from an Excel file."""
        pass

    def from_epds(self, filepaths: list[str]):
        """Load an inventory from an EPD file."""
        pass