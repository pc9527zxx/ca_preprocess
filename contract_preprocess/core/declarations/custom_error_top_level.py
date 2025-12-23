from typing import TYPE_CHECKING

from contract_preprocess.core.declarations.custom_error import CustomError
from contract_preprocess.core.declarations.top_level import TopLevel

if TYPE_CHECKING:
    from contract_preprocess.core.compilation_unit import CompilationUnitWrapper
    from contract_preprocess.core.scope.scope import FileScope


class CustomErrorTopLevel(CustomError, TopLevel):
    def __init__(self, compilation_unit: "CompilationUnit", scope: "FileScope") -> None:
        super().__init__(compilation_unit)
        self.file_scope: "FileScope" = scope

    @property
    def canonical_name(self) -> str:
        return self.full_name
