from typing import List, Optional, Union

from contract_preprocess.ir.operations.call import Call
from contract_preprocess.ir.operations.lvalue import OperationWithLValue

from contract_preprocess.ir.utils.utils import is_valid_lvalue

from contract_preprocess.core.declarations.structure import Structure
from contract_preprocess.core.declarations.structure_contract import StructureContract
from contract_preprocess.ir.variables.constant import Constant
from contract_preprocess.ir.variables.temporary import TemporaryVariable
from contract_preprocess.ir.variables.temporary_ssa import TemporaryVariableSSA


class NewStructure(Call, OperationWithLValue):
    def __init__(
        self,
        structure: StructureContract,
        lvalue: Union[TemporaryVariableSSA, TemporaryVariable],
        names: Optional[List[str]] = None,
    ) -> None:
        """
        #### Parameters
        names -
            For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
            Otherwise, None.
        """
        super().__init__(names=names)
        assert isinstance(structure, Structure)
        assert is_valid_lvalue(lvalue)
        self._structure = structure
        # todo create analyze to add the contract instance
        self._lvalue = lvalue

    @property
    def read(self) -> List[Union[TemporaryVariableSSA, TemporaryVariable, Constant]]:
        return self._unroll(self.arguments)

    @property
    def structure(self) -> StructureContract:
        return self._structure

    @property
    def structure_name(self):
        return self.structure.name

    def __str__(self):
        args = [str(a) for a in self.arguments]
        lvalue = self.lvalue
        return f"{lvalue}({lvalue.type}) = new {self.structure_name}({','.join(args)})"
