from typing import TYPE_CHECKING

from contract_preprocess.core.declarations.top_level import TopLevel
from contract_preprocess.utils.using_for import USING_FOR

if TYPE_CHECKING:
    from contract_preprocess.core.scope.scope import FileScope


class UsingForTopLevel(TopLevel):
    def __init__(self, scope: "FileScope") -> None:
        super().__init__()
        self._using_for: USING_FOR = {}
        self.file_scope: "FileScope" = scope

    @property
    def using_for(self) -> USING_FOR:
        return self._using_for
