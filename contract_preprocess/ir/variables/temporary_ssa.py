"""
    This class is used for the SSA version of the IR
    It is similar to the non-SSA version of the IR
    as the TemporaryVariable are in SSA form in both version
"""
from typing import Union
from contract_preprocess.ir.variables.temporary import TemporaryVariable
from contract_preprocess.ir.variables.reference import ReferenceVariable
from contract_preprocess.ir.variables.tuple import TupleVariable


class TemporaryVariableSSA(TemporaryVariable):  # pylint: disable=too-few-public-methods
    def __init__(self, temporary: TemporaryVariable) -> None:
        super().__init__(temporary.node, temporary.index)

        self._non_ssa_version = temporary

    @property
    def non_ssa_version(self) -> Union[TemporaryVariable, TupleVariable, ReferenceVariable]:
        return self._non_ssa_version
