from contract_preprocess.exceptions import PreprocessException


class ParsingError(PreprocessException):
    pass


class VariableNotFound(PreprocessException):
    pass
