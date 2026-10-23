"""
Base text normalization module with common utilities.
"""
import re
from abc import ABC, abstractmethod
from typing import Optional


class BaseNormalizer(ABC):
    """Abstract base class for text normalizers."""
    
    def __init__(self, locale: str):
        self.locale = locale
        self._compile_patterns()
    
    @abstractmethod
    def _compile_patterns(self):
        """Compile regex patterns for the specific language."""
        pass
    
    @abstractmethod
    def normalize(self, text: str) -> str:
        """Normalize text according to language rules."""
        pass
    
    def _normalize_whitespace(self, s: str) -> str:
        """Normalize whitespace across all languages."""
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"\s+([.,!?;:।])", r"\1", s)
        s = re.sub(r"([(\[{])\s+", r"\1", s)
        s = re.sub(r"\s+([)\]}])", r"\1", s)
        return s
    
    def _normalize_quotes(self, s: str) -> str:
        """Normalize quotes to standard forms."""
        return (
            s.replace("\u201c", "\"")
            .replace("\u201d", "\"")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )
    
    def _normalize_dots(self, s: str) -> str:
        """Normalize multiple consecutive dots (more than 2) to a single dot."""
        return re.sub(r"\.{3,}", ".", s)

    def _normalize_dso(self, s: str) -> str:
        """Normalize DSO variants (d.s.o., d s o, DSO, etc.) to 'D S O'."""
        return re.sub(
            r"(?<![A-Za-z0-9])d\s*\.?\s*s\s*\.?\s*o\s*\.?(?![A-Za-z0-9])",
            "D S O",
            s,
            flags=re.IGNORECASE,
        )
    
    @staticmethod
    def pluralize(word_singular: str, word_plural: str, count: int) -> str:
        """Return singular or plural form based on count."""
        return word_singular if count == 1 else word_plural


def create_normalizer(locale: str = "en-IN", **kwargs):
    """Factory function to create appropriate normalizer based on locale."""
    if locale.startswith("hi"):
        from .hi_normalizer import HindiNormalizer
        return HindiNormalizer(locale, **kwargs)
    elif locale.startswith("en"):
        from .en_normalizer import EnglishNormalizer
        return EnglishNormalizer(locale, **kwargs)
    else:
        raise ValueError(f"Unsupported locale: {locale}")
