"""Utilities for deterministic Indonesian clinical text normalization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_RESOURCE_DIR = Path("data/input")


@dataclass
class NormalizationStep:
    name: str
    before: str
    after: str


@dataclass
class NormalizationResult:
    original_text: str
    normalized_text: str
    steps: list[NormalizationStep] = field(default_factory=list)
    replacements: dict[str, int] = field(default_factory=dict)


def load_json_dict(path: str | Path) -> dict[str, str]:
    """Load a simple string-to-string JSON dictionary."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object mapping in {path}")
    return {str(key): str(value) for key, value in data.items()}


class IndonesianClinicalNormalizer:
    """Rule-based normalizer for early Indonesian clinical NLP experiments."""

    def __init__(
        self,
        abbreviations: dict[str, str] | None = None,
        typos: dict[str, str] | None = None,
        units: dict[str, str] | None = None,
    ) -> None:
        self.abbreviations = {k.casefold(): v for k, v in (abbreviations or {}).items()}
        self.typos = {k.casefold(): v for k, v in (typos or {}).items()}
        self.units = {k.casefold(): v for k, v in (units or {}).items()}

    @classmethod
    def from_resource_dir(cls, resource_dir: str | Path = DEFAULT_RESOURCE_DIR) -> "IndonesianClinicalNormalizer":
        resource_path = Path(resource_dir)
        return cls(
            abbreviations=load_json_dict(resource_path / "id_abbreviations.json"),
            typos=load_json_dict(resource_path / "id_typos.json"),
            units=load_json_dict(resource_path / "id_units.json"),
        )

    def normalize(self, text: str, audit: bool = False) -> NormalizationResult:
        original = "" if text is None else str(text)
        steps: list[NormalizationStep] = []
        replacements: dict[str, int] = {}

        current = original
        current = self._record_step("unicode_and_case", current, self._unicode_and_case(current), steps)
        current = self._record_step("separator_spacing", current, self._normalize_separators(current), steps)
        current, count = self._replace_dictionary(current, self.typos, "typo")
        replacements["typo"] = count
        if count:
            steps.append(NormalizationStep("typo_replacement", steps[-1].after if steps else original, current))
        before_abbrev = current
        current, count = self._replace_dictionary(current, self.abbreviations, "abbreviation")
        replacements["abbreviation"] = count
        if count:
            steps.append(NormalizationStep("abbreviation_expansion", before_abbrev, current))
        before_units = current
        current, count = self._replace_dictionary(current, self.units, "unit")
        replacements["unit"] = count
        if count:
            steps.append(NormalizationStep("unit_normalization", before_units, current))
        current = self._record_step("final_spacing", current, self._final_spacing(current), steps)

        if not audit:
            steps = []
        return NormalizationResult(original_text=original, normalized_text=current, steps=steps, replacements=replacements)

    @staticmethod
    def _record_step(name: str, before: str, after: str, steps: list[NormalizationStep]) -> str:
        if before != after:
            steps.append(NormalizationStep(name, before, after))
        return after

    @staticmethod
    def _unicode_and_case(text: str) -> str:
        translation = {
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u00a0": " ",
        }
        for source, target in translation.items():
            text = text.replace(source, target)
        return text.casefold().strip()

    @staticmethod
    def _normalize_separators(text: str) -> str:
        text = re.sub(r"\s*/\s*", "/", text)
        text = re.sub(r"\s*%\s*", "%", text)
        text = re.sub(r"\s*,\s*", ", ", text)
        text = re.sub(r"\s*;\s*", "; ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _final_spacing(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([,.;:%])", r"\1", text)
        text = re.sub(r"([,;])(?=\S)", r"\1 ", text)
        text = text.replace("x / menit", "x/menit")
        return text.strip()

    @staticmethod
    def _replace_dictionary(text: str, mapping: dict[str, str], label: str) -> tuple[str, int]:
        count = 0
        current = text
        for source, target in sorted(mapping.items(), key=lambda item: (-len(item[0]), item[0])):
            pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(source)}(?![A-Za-z0-9])", re.IGNORECASE)
            current, replaced = pattern.subn(target, current)
            count += replaced
        return current, count


def normalize_text(text: str, resource_dir: str | Path = DEFAULT_RESOURCE_DIR) -> str:
    return IndonesianClinicalNormalizer.from_resource_dir(resource_dir).normalize(text).normalized_text
