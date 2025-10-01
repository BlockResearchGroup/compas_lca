import yaml
from pathlib import Path
from typing import Any
from typing import Dict
from .context import Context
from .agent_settings import AgentSettings
from .agent import CompasAgent

def _deep_get(d: Dict[str, Any], *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
        if d is None:
            return default
    return d if d is not None else default

def load_settings(cfg_path: str | Path) -> AgentSettings:
    cfg = yaml.safe_load(Path(cfg_path).read_text(encoding="utf-8"))
    agent_cfg = cfg.get("agent", {}) or {}

    provider: str = agent_cfg.get("provider", "openai")
    model: str = agent_cfg.get("model")
    if not model:
        raise ValueError("config.yaml -> agent.model is required")

    retries: int = int(agent_cfg.get("retries", 1))
    currency: str = agent_cfg.get("currency", "USD")
    agent_ms: Dict[str, Any] = agent_cfg.get("model_settings") or {}

    model_block: Dict[str, Any] = _deep_get(cfg, "models", provider, model, default={}) or {}
    pricing: Dict[str, Any] = model_block.get("pricing") or {}
    model_ms: Dict[str, Any] = model_block.get("model_settings") or {}
    merged_ms = {**model_ms, **agent_ms}

    pricing_table = {
        model: {
            "in_per_1k": float(pricing.get("in_per_1k", 0.0)),
            "out_per_1k": float(pricing.get("out_per_1k", 0.0)),
        }
    }

    return AgentSettings(
        model=model,
        retries=retries,
        currency=currency,
        model_settings=merged_ms,
        pricing_table=pricing_table,
    )

CONFIG_PATH = Path("config.yaml")

def load_agent(cfg_path: Path | str = CONFIG_PATH, *, context: Context) -> CompasAgent:
    """
    Create a CompasAgent from a config file and optional context.
    If cfg_path is not provided, defaults to "config.yaml".
    """    
    settings = load_settings(cfg_path)
    return CompasAgent(settings=settings, context=context)
