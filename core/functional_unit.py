from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitData:
    """
    DF-LCA functional unit: unit data.

    The paper distinguishes LCA's functional unit (unit product/service) from DF-LCA's
    unit data. In this scaffold we support normalization by bytes and by (estimated) tokens.
    """

    input_bytes: int = 0
    output_bytes: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_bytes(self) -> int:
        return max(0, self.input_bytes) + max(0, self.output_bytes)

    @property
    def total_tokens(self) -> int:
        return max(0, self.input_tokens) + max(0, self.output_tokens)

