"""
This module import all contract_preprocess exceptions
"""
# pylint: disable=unused-import
from contract_preprocess.ir.exceptions import IRError
from contract_preprocess.solc_parsing.exceptions import ParsingError, VariableNotFound
from contract_preprocess.core.exceptions import CoreError
from contract_preprocess.exceptions import PreprocessException
