from contract_preprocess.core.variables.structure_variable import StructureVariable
from contract_preprocess.vyper_parsing.type_parsing import parse_type
from contract_preprocess.vyper_parsing.ast.types import AnnAssign


class StructureVariableVyper:
    def __init__(self, variable: StructureVariable, variable_data: AnnAssign):
        self._variable: StructureVariable = variable
        self._variable.name = variable_data.target.id
        self._elem_to_parse = variable_data.annotation

    @property
    def underlying_variable(self) -> StructureVariable:
        return self._variable

    def analyze(self, contract) -> None:
        self._variable.type = parse_type(self._elem_to_parse, contract)
