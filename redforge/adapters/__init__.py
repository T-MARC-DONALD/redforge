"""redforge.adapters - talk to any LLM provider through one interface.

Public API:
    build_adapter(target_config) -> BaseAdapter
    adapter.complete(conversation) -> AdapterResponse
"""
from redforge.adapters.base import AdapterError, BaseAdapter
from redforge.adapters.factory import build_adapter

__all__ = ["BaseAdapter", "AdapterError", "build_adapter"]
