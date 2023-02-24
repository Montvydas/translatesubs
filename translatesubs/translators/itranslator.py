from typing import List, Iterator
from translatesubs.translators.translated import Translated
from translatesubs.translators.language import Language
from abc import ABC, abstractmethod


class ITranslator(ABC):
    @abstractmethod
    def translate(self, text: List[str], to_lang: str) -> Iterator[Translated]:
        pass

    @abstractmethod
    def detect_language(self, to_lang: str) -> Language:
        pass

    @abstractmethod
    def get_supported(self) -> str:
        pass

    @abstractmethod
    def get_char_limit(self) -> int:
        pass
