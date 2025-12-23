"""
    EventTopLevel module
"""
from typing import TYPE_CHECKING, Dict

from contract_preprocess.core.declarations.event_top_level import EventTopLevel
from contract_preprocess.core.variables.event_variable import EventVariable
from contract_preprocess.core.compilation_unit import CompilationUnitWrapper
from contract_preprocess.solc_parsing.variables.event_variable import EventVariableSolc
from contract_preprocess.solc_parsing.declarations.caller_context import CallerContextExpression

if TYPE_CHECKING:
    from contract_preprocess.solc_parsing.compilation_unit_solc import SolcCompilationUnitParser


class EventTopLevelSolc(CallerContextExpression):
    """
    EventTopLevel class
    """

    def __init__(
        self, event: EventTopLevel, event_data: Dict, parser: "SolcCompilationUnitParser"
    ) -> None:

        self._event = event
        self._parser = parser

        if self.is_compact_ast:
            self._event.name = event_data["name"]
            elems = event_data["parameters"]
            assert elems["nodeType"] == "ParameterList"
            self._elemsNotParsed = elems["parameters"]
        else:
            self._event.name = event_data["attributes"]["name"]
            for elem in event_data["children"]:
                # From Solidity 0.6.3 to 0.6.10 (included)
                # Comment above a event might be added in the children
                # of an event for the legacy ast
                if elem["name"] == "ParameterList":
                    if "children" in elem:
                        self._elemsNotParsed = elem["children"]
                    else:
                        self._elemsNotParsed = []

    def analyze(self) -> None:
        for elem_to_parse in self._elemsNotParsed:
            elem = EventVariable()
            # Todo: check if the source offset is always here
            if "src" in elem_to_parse:
                elem.set_offset(elem_to_parse["src"], self._parser.compilation_unit)
            elem_parser = EventVariableSolc(elem, elem_to_parse)
            elem_parser.analyze(self)

            self._event.elems.append(elem)

        self._elemsNotParsed = []

    @property
    def is_compact_ast(self) -> bool:
        return self._parser.is_compact_ast

    @property
    def compilation_unit(self) -> CompilationUnitWrapper:
        return self._parser.compilation_unit

    def get_key(self) -> str:
        return self._parser.get_key()

    @property
    def parser(self) -> "SolcCompilationUnitParser":
        return self._parser

    @property
    def underlying_event(self) -> EventTopLevel:
        return self._event
