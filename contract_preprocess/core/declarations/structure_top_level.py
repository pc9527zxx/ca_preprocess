from typing import TYPE_CHECKING

from contract_preprocess.core.declarations import Structure
from contract_preprocess.core.declarations.top_level import TopLevel

if TYPE_CHECKING:
    from contract_preprocess.core.scope.scope import FileScope
    from contract_preprocess.core.compilation_unit import CompilationUnitWrapper


class StructureTopLevel(Structure, TopLevel):
    def __init__(self, compilation_unit: "CompilationUnit", scope: "FileScope") -> None:
        super().__init__(compilation_unit)
        self.file_scope: "FileScope" = scope
