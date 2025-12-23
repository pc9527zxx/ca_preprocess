from typing import Dict, TYPE_CHECKING

from contract_preprocess.core.variables.top_level_variable import TopLevelVariable
from contract_preprocess.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from contract_preprocess.solc_parsing.declarations.caller_context import CallerContextExpression

if TYPE_CHECKING:
    from contract_preprocess.solc_parsing.compilation_unit_solc import SolcCompilationUnitParser
    from contract_preprocess.core.compilation_unit import CompilationUnitWrapper


class TopLevelVariableSolc(VariableDeclarationSolc, CallerContextExpression):
    def __init__(
        self,
        variable: TopLevelVariable,
        variable_data: Dict,
        parser: "SolcCompilationUnitParser",
    ) -> None:
        super().__init__(variable, variable_data)
        self._parser = parser

    @property
    def is_compact_ast(self) -> bool:
        return self._parser.is_compact_ast

    @property
    def compilation_unit(self) -> "CompilationUnitWrapper":
        return self._parser.compilation_unit

    def get_key(self) -> str:
        return self._parser.get_key()

    @property
    def parser(self) -> "SolcCompilationUnitParser":
        return self._parser

    @property
    def underlying_variable(self) -> TopLevelVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, TopLevelVariable)
        return self._variable
