from typing import List


from contract_preprocess.core.variables.variable import Variable
from contract_preprocess.ir.operations import Operation


class Nop(Operation):
    @property
    def read(self) -> List[Variable]:
        return []

    @property
    def used(self):
        return []

    def __str__(self):
        return "NOP"
