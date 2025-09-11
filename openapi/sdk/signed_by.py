from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum, auto
from typing import NamedTuple


class SignatureMode(Enum):
    HEADER = auto()
    QUERY = auto()


class SignedBy(ABC):
    @property
    @abstractmethod
    def mode(self) -> SignatureMode:
        pass


class SignedByHeader(SignedBy):
    @property
    def mode(self) -> SignatureMode:
        return SignatureMode.HEADER


class QuerySignatureParams(NamedTuple):
    duration: int


class SignedByQuery(SignedBy):
    @property
    def mode(self) -> SignatureMode:
        return SignatureMode.QUERY

    _parameters: Optional[QuerySignatureParams]

    def __init__(self, parameters: Optional[QuerySignatureParams] = None):
        self._parameters = parameters

    @property
    def parameters(self) -> Optional[QuerySignatureParams]:
        return self._parameters
