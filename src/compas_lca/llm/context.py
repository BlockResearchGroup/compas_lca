from dataclasses import dataclass

from typing import Any
from typing import Optional
from typing import Dict
from typing import Type
from typing import Callable
from typing import Iterable

@dataclass
class Context:
    """
    The Context object specifies all runtime parameters that shape how the
    underlying `pydantic_ai.Agent` is constructed and executed. It can define
    prompt instructions, expected output schemas, auxiliary tool resources, and
    optional user-defined metadata such as a run name or attached tools.

    Parameters
    ----------
    instructions : str, optional
        Natural-language instructions provided to the agent (i.e., the prompt).
    output_type : Type, optional
        Expected Python type or Pydantic model for validating the agent's output.
        Defaults to `str` if unspecified.
    tool_resources_type : Type, optional
        Type defining the dependency/resource object passed to tool functions
        registered with the agent. This becomes the `deps_type` of the
        underlying Pydantic agent.
    name : str, optional
        Human-readable label for this agent or run. Useful for logging or
        multi-agent workflows.
    tools : Iterable[Callable], optional
        A list of callable tool functions to be registered on the agent.
    """

    instructions: Optional[str] = None
    output_type: Optional[Type] = str
    tool_resources_type: Optional[Type] = None
    name: Optional[str] = None
    tools: Optional[Iterable[Callable]] = None

    def to_pydantic_agent_kwargs(self) -> Dict[str, Any]:
        """
        Converts context into a dictionary of keyword arguments
        accepted by 'pydantic_ai.Agent.__init__'.

        Returns:
            A dictionary with keys matching the Pydantic Agent constructor:
            - 'instructions'
            - 'output_type'
            - 'deps_type' (from 'tool_resources_type')
            - 'name'
        """
        return dict(
            output_type=self.output_type or str,
            instructions=self.instructions,
            deps_type=self.tool_resources_type,  # key must match pydantic_ai.Agent API (deps_type)
            name=self.name,
        )
