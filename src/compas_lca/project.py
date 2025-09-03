class Project:
    """A Life Cycle Assessment (LCA) project."""
    def __init__(self, name: str, config=None):
        self.name = name
        self.config = config

    def run(self):
        pass