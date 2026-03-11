from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DPUProcess(str, Enum):
    computing = "computing"
    create = "create"
    storage = "storage"
    transfer = "transfer"


class DPUNode(BaseModel):
    """
    Data Processing Unit (DPU) definition (paper: DPU = {Id, Name, Type, ...}).

    This is a lightweight representation suitable for storing as an artifact along
    with evaluation runs.
    """

    id: str
    name: str
    type: str = Field(description="Logical type of DPU, e.g., device/service/model endpoint")

    output: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[Dict[str, Any]] = Field(default_factory=list)
    processes: List[DPUProcess] = Field(default_factory=list)

    indicators: Dict[str, Any] = Field(
        default_factory=dict, description="Collected indicators/metrics for this DPU"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Hardware/VE context used for inventory analysis"
    )
    subnodes: List["DPUNode"] = Field(default_factory=list)


DPUNode.model_rebuild()

