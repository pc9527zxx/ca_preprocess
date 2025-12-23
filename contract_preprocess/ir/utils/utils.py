from typing import Union, Optional

from contract_preprocess.core.variables.local_variable import LocalVariable
from contract_preprocess.core.variables.state_variable import StateVariable

from contract_preprocess.core.declarations.solidity_variables import SolidityVariable
from contract_preprocess.core.variables.top_level_variable import TopLevelVariable

from contract_preprocess.ir.variables.temporary import TemporaryVariable
from contract_preprocess.ir.variables.constant import Constant
from contract_preprocess.ir.variables.reference import ReferenceVariable
from contract_preprocess.ir.variables.tuple import TupleVariable
from contract_preprocess.core.source_mapping.source_mapping import SourceMapping

RVALUE = Union[
    StateVariable,
    LocalVariable,
    TopLevelVariable,
    TemporaryVariable,
    Constant,
    SolidityVariable,
    ReferenceVariable,
]

LVALUE = Union[
    StateVariable,
    LocalVariable,
    TemporaryVariable,
    ReferenceVariable,
    TupleVariable,
]


def is_valid_rvalue(v: Optional[SourceMapping]) -> bool:
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TopLevelVariable,
            TemporaryVariable,
            Constant,
            SolidityVariable,
            ReferenceVariable,
        ),
    )


def is_valid_lvalue(v: Optional[SourceMapping]) -> bool:
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            ReferenceVariable,
            TupleVariable,
        ),
    )
