from typing import Optional, TYPE_CHECKING

from contract_preprocess.ir.variables.variable import IRVariable

if TYPE_CHECKING:
    from contract_preprocess.core.cfg.node import Node


class TupleVariable(IRVariable):
    def __init__(self, node: "Node", index: Optional[int] = None) -> None:
        super().__init__()
        if index is None:
            self._index = node.compilation_unit.counter_ir_tuple
            node.compilation_unit.counter_ir_tuple += 1
        else:
            self._index = index

        self._node = node

    @property
    def node(self) -> "Node":
        return self._node

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def name(self) -> str:
        return f"TUPLE_{self.index}"

    def __str__(self) -> str:
        return self.name
