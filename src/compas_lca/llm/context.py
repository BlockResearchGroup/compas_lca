class Context:
    """A context for an LLM agent to execute tasks."""

    def __init__(self, tools, data):
        self.messages = []
        self.tools = tools
        self.data = data
