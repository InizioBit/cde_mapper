"""Deterministic Indonesian clinical text normalization.

The module intentionally uses only the Python standard library so Stage 1 can
run before the retrieval, embedding, or LLM stack is initialized.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal


DEFAULT_RESOURCE_DIR = Path("data/input")
NORMALIZER_VERSION = "1.0.0"
Profile = Literal["clinical", "question", "answer"]


@dataclass
class NormalizationStep:
    name: str
    before: str
    after: str


@dataclass
class NormalizationChange:
    kind: str
    source: str
    target: str
    count: int = 1
    status: str = "automatic"
    rule: str | None = None


@dataclass
class NormalizationResult:
    original_text: str
    normalized_text: str
    sentences: list[str] = field(default_factory=list)
    steps: list[NormalizationStep] = field(default_factory=list)
    changes: list[NormalizationChange] = field(default_factory=list)
    replacements: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    boilerplate: list[str] = field(default_factory=list)
    content_text: str = ""
    profile: str = "clinical"
    normalizer_version: str = NORMALIZER_VERSION
    resource_version: str = "legacy-flat"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AbbreviationEntry:
    abbreviation: str
    expansion: str
    status: str = "automatic"
    contexts: tuple[str, ...] = ()
    warning: str | None = None
    layer: str = "legacy"


def load_json_dict(path: str | Path) -> dict[str, str]:
    """Load a simple string-to-string JSON dictionary."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object mapping in {path}")
    return {str(key): str(value) for key, value in data.items()}


def _load_abbreviation_master(path: Path) -> tuple[list[AbbreviationEntry], str]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    layers = data.get("layers")
    if not isinstance(layers, dict):
        raise ValueError(f"Expected layered abbreviation mapping in {path}")

    entries: list[AbbreviationEntry] = []
    for layer, raw_entries in layers.items():
        if layer == "ambiguous_not_automatic":
            continue
        for raw in raw_entries:
            expansion = raw.get("expansion")
            if not expansion:
                continue
            entries.append(
                AbbreviationEntry(
                    abbreviation=str(raw["abbr"]),
                    expansion=str(expansion),
                    status=str(raw.get("status", "review_required")),
                    contexts=tuple(str(value) for value in raw.get("context", [])),
                    warning=raw.get("warning"),
                    layer=layer,
                )
            )
    return entries, str(data.get("schema_version", "unknown"))


class IndonesianClinicalNormalizer:
    """Rule-based, auditable normalizer for Indonesian clinical text."""

    _INFORMAL_LAYER = "informal_conversation"
    _BOILERPLATE_PATTERNS = (
        re.compile(r"^(?:alo|halo|hai)(?:\s+[\w.'-]+){0,3}[,!.:\s-]*", re.IGNORECASE),
        re.compile(r"^(?:waalaikumsalam|wa alaikumsalam)[,!.:\s-]*", re.IGNORECASE),
        re.compile(
            r"(?:demikian (?:informasi|penjelasan)[^.?!]*[.?!]?|"
            r"semoga (?:bermanfaat|membantu|menjawab)[^.?!]*[.?!]?|"
            r"terima kasih[.!]?)\s*$",
            re.IGNORECASE,
        ),
    )

    def __init__(
        self,
        abbreviations: dict[str, str] | None = None,
        typos: dict[str, str] | None = None,
        units: dict[str, str] | None = None,
        abbreviation_entries: Iterable[AbbreviationEntry] | None = None,
        resource_version: str = "legacy-flat",
    ) -> None:
        if abbreviation_entries is None:
            abbreviation_entries = (
                AbbreviationEntry(key, value) for key, value in (abbreviations or {}).items()
            )
        self.abbreviation_entries = sorted(
            abbreviation_entries,
            key=lambda entry: (-len(entry.abbreviation), entry.abbreviation.casefold()),
        )
        self.typos = {key.casefold(): value for key, value in (typos or {}).items()}
        self.units = {key.casefold(): value for key, value in (units or {}).items()}
        self.resource_version = resource_version

    @classmethod
    def from_resource_dir(
        cls, resource_dir: str | Path = DEFAULT_RESOURCE_DIR
    ) -> "IndonesianClinicalNormalizer":
        resource_path = Path(resource_dir)
        master_path = resource_path / "id_abbreviations_layered.json"
        if master_path.exists():
            entries, resource_version = _load_abbreviation_master(master_path)
            abbreviations = None
        else:
            entries = None
            resource_version = "legacy-flat"
            abbreviations = load_json_dict(resource_path / "id_abbreviations.json")
        return cls(
            abbreviations=abbreviations,
            abbreviation_entries=entries,
            typos=load_json_dict(resource_path / "id_typos.json"),
            units=load_json_dict(resource_path / "id_units.json"),
            resource_version=resource_version,
        )

    def normalize(
        self, text: str | None, audit: bool = False, profile: Profile = "clinical"
    ) -> NormalizationResult:
        if profile not in {"clinical", "question", "answer"}:
            raise ValueError("profile must be one of: clinical, question, answer")

        original = "" if text is None else str(text)
        steps: list[NormalizationStep] = []
        changes: list[NormalizationChange] = []
        warnings: list[str] = []
        replacements = {"typo": 0, "abbreviation": 0, "unit": 0}

        current = self._record_step(
            "unicode_and_case", original, self._unicode_and_case(original), steps
        )
        current = self._record_step(
            "control_and_spacing", current, self._clean_controls_and_spacing(current), steps
        )
        current = self._record_step(
            "punctuation", current, self._normalize_punctuation(current), steps
        )

        current, typo_changes = self._replace_mapping(current, self.typos, "typo")
        changes.extend(typo_changes)
        replacements["typo"] = sum(change.count for change in typo_changes)
        if typo_changes:
            before = steps[-1].after if steps else original
            steps.append(NormalizationStep("typo_replacement", before, current))

        before_abbreviations = current
        current, abbreviation_changes, abbreviation_warnings = self._expand_abbreviations(
            current, profile
        )
        changes.extend(abbreviation_changes)
        warnings.extend(abbreviation_warnings)
        replacements["abbreviation"] = sum(
            change.count for change in abbreviation_changes
        )
        if abbreviation_changes:
            steps.append(
                NormalizationStep(
                    "abbreviation_expansion", before_abbreviations, current
                )
            )

        before_units = current
        current = self._space_number_units(current)
        current, unit_changes = self._replace_mapping(current, self.units, "unit")
        changes.extend(unit_changes)
        replacements["unit"] = sum(change.count for change in unit_changes)
        if current != before_units:
            steps.append(NormalizationStep("unit_normalization", before_units, current))

        current = self._record_step(
            "final_spacing", current, self._final_spacing(current), steps
        )
        sentences = self.segment_sentences(current)
        boilerplate: list[str] = []
        content_text = current
        if profile == "answer":
            content_text, boilerplate = self._extract_boilerplate(current)

        if not audit:
            steps = []
            changes = []
        return NormalizationResult(
            original_text=original,
            normalized_text=current,
            sentences=sentences,
            steps=steps,
            changes=changes,
            replacements=replacements,
            warnings=list(dict.fromkeys(warnings)),
            boilerplate=boilerplate,
            content_text=content_text,
            profile=profile,
            resource_version=self.resource_version,
        )

    @staticmethod
    def _record_step(
        name: str, before: str, after: str, steps: list[NormalizationStep]
    ) -> str:
        if before != after:
            steps.append(NormalizationStep(name, before, after))
        return after

    @staticmethod
    def _unicode_and_case(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"(?<=[a-z]{3})(?=[A-Z][a-z])", " ", text)
        translation = str.maketrans(
            {
                "\u2013": "-",
                "\u2014": "-",
                "\u2018": "'",
                "\u2019": "'",
                "\u201c": '"',
                "\u201d": '"',
                "\u00a0": " ",
            }
        )
        return text.translate(translation).casefold().strip()

    @staticmethod
    def _clean_controls_and_spacing(text: str) -> str:
        text = "".join(
            character
            for character in text
            if character in "\n\t" or unicodedata.category(character) != "Cc"
        )
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n+ *", "\n", text)
        return text.strip()

    @staticmethod
    def _normalize_punctuation(text: str) -> str:
        text = re.sub(r"([!?])\1{1,}", r"\1", text)
        text = re.sub(r"\.{2,}", ".", text)
        text = re.sub(r"(?<!\d)([.!?])(?=[a-z])", r"\1 ", text)
        text = re.sub(r"(?<=\w)\((?=\w)", " (", text)
        text = re.sub(r"\s*/\s*", "/", text)
        text = re.sub(r"\s*%\s*", "%", text)
        text = IndonesianClinicalNormalizer._normalize_commas(text)
        text = re.sub(r"\s*;\s*", "; ", text)
        return text

    @staticmethod
    def _normalize_commas(text: str) -> str:
        """Preserve decimal commas while spacing punctuation commas."""
        output: list[str] = []
        index = 0
        while index < len(text):
            if text[index] != ",":
                output.append(text[index])
                index += 1
                continue
            previous = output[-1] if output else ""
            next_index = index + 1
            while next_index < len(text) and text[next_index].isspace():
                next_index += 1
            following = text[next_index] if next_index < len(text) else ""
            if previous.isdigit() and following.isdigit():
                output.append(",")
            else:
                while output and output[-1] == " ":
                    output.pop()
                output.append(",")
                if following:
                    output.append(" ")
            index = next_index
        return "".join(output)

    @staticmethod
    def _token_pattern(source: str) -> re.Pattern[str]:
        return re.compile(
            rf"(?<![^\W_]){re.escape(source)}(?![^\W_])",
            re.IGNORECASE | re.UNICODE,
        )

    def _replace_mapping(
        self, text: str, mapping: dict[str, str], kind: str
    ) -> tuple[str, list[NormalizationChange]]:
        current = text
        changes: list[NormalizationChange] = []
        for source, target in sorted(
            mapping.items(), key=lambda item: (-len(item[0]), item[0])
        ):
            current, count = self._token_pattern(source).subn(target, current)
            if count:
                changes.append(
                    NormalizationChange(
                        kind=kind, source=source, target=target, count=count
                    )
                )
        return current, changes

    def _expand_abbreviations(
        self, text: str, profile: Profile
    ) -> tuple[str, list[NormalizationChange], list[str]]:
        current = text
        changes: list[NormalizationChange] = []
        warnings: list[str] = []
        for entry in self.abbreviation_entries:
            if entry.status == "review_required":
                continue
            if profile == "answer" and entry.layer == self._INFORMAL_LAYER:
                continue

            pattern = self._token_pattern(entry.abbreviation)
            matches = list(pattern.finditer(current))
            if not matches:
                continue

            replacement_count = 0
            chunks: list[str] = []
            cursor = 0
            for match in matches:
                chunks.append(current[cursor : match.start()])
                window = current[max(0, match.start() - 45) : match.end() + 45]
                if entry.status == "automatic" or self._context_matches(entry, window):
                    chunks.append(entry.expansion)
                    replacement_count += 1
                else:
                    chunks.append(match.group(0))
                    warnings.append(
                        f"Singkatan ambigu '{match.group(0)}' dipertahankan; "
                        f"konteks untuk '{entry.expansion}' tidak cukup."
                    )
                cursor = match.end()
            chunks.append(current[cursor:])
            current = "".join(chunks)
            if replacement_count:
                changes.append(
                    NormalizationChange(
                        kind="abbreviation",
                        source=entry.abbreviation,
                        target=entry.expansion,
                        count=replacement_count,
                        status=entry.status,
                        rule=entry.layer,
                    )
                )
        return current, changes, warnings

    @staticmethod
    def _context_matches(entry: AbbreviationEntry, window: str) -> bool:
        token = entry.abbreviation.casefold()
        local = window.casefold()
        rules = {
            "bb": r"\b\d+(?:[.,]\d+)?\s*kg\b|\b(?:berat|antropometri)\b",
            "tb": r"\b\d+(?:[.,]\d+)?\s*cm\b|\b(?:tinggi|antropometri)\b",
            "px": r"\bpx\s+(?:dgn|dg|dengan|usia|umur|mengalami|menderita)\b",
            "n": r"\bn\s*\d{2,3}\b|\b\d{2,3}\s*x/menit\b",
            "rr": r"\brr\s*\d{1,3}\b|\b(?:napas|nafas|respirasi)\b",
            "temp": r"\btemp\s*\d{2}(?:[.,]\d+)?\b|\b(?:suhu|derajat)\b",
            "kb": r"\b(?:kontrasepsi|pil|suntik|spiral|iud|kehamilan)\b",
            "th": r"\b(?:usia|umur)\s*\d+\s*th\b|\b\d+\s*th\b",
        }
        if token in rules:
            return bool(re.search(rules[token], local, re.IGNORECASE))
        return any(context.casefold() in local for context in entry.contexts)

    @staticmethod
    def _space_number_units(text: str) -> str:
        units = r"(?:mcg|µg|mg|g|kg|ml|l|cm|mm|mmhg|mg/dl|g/dl)"
        return re.sub(
            rf"(?<=\d)\s*({units})\b", r" \1", text, flags=re.IGNORECASE
        )

    @staticmethod
    def _final_spacing(text: str) -> str:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\s+([,.;:%!?])", r"\1", text)
        text = IndonesianClinicalNormalizer._normalize_commas(text)
        text = re.sub(r";(?=\S)", r"; ", text)
        text = text.replace("x / menit", "x/menit")
        return text.strip()

    @staticmethod
    def segment_sentences(text: str) -> list[str]:
        """Segment conservatively without splitting decimal numbers."""
        if not text:
            return []
        prepared = re.sub(
            r"(?<=[a-z])([.!?])(?=[a-z])", r"\1 ", text, flags=re.IGNORECASE
        )
        parts = re.split(r"\n+|(?<!\d)(?<=[.!?])\s+(?!\d)", prepared)
        return [part.strip() for part in parts if part.strip()]

    def _extract_boilerplate(self, text: str) -> tuple[str, list[str]]:
        content = text
        removed: list[str] = []
        for pattern in self._BOILERPLATE_PATTERNS:
            match = pattern.search(content)
            if match:
                value = match.group(0).strip()
                if value:
                    removed.append(value)
                content = (content[: match.start()] + content[match.end() :]).strip()
        return content, removed


def normalize_text(
    text: str,
    resource_dir: str | Path = DEFAULT_RESOURCE_DIR,
    profile: Profile = "clinical",
) -> str:
    """Backward-compatible convenience function returning normalized text."""
    return (
        IndonesianClinicalNormalizer.from_resource_dir(resource_dir)
        .normalize(text, profile=profile)
        .normalized_text
    )


def normalize_queries(
    queries: list[Any],
    resource_dir: str | Path = DEFAULT_RESOURCE_DIR,
    profile: Profile = "clinical",
) -> list[Any]:
    """Normalize QueryDecomposedModel items while preserving original_label.

    Both plain model lists and the repository's ``(gold_id, model)`` tuples are
    supported. The input list is updated in place and returned for convenience.
    """
    normalizer = IndonesianClinicalNormalizer.from_resource_dir(resource_dir)
    for item in queries:
        query = item[1] if isinstance(item, tuple) and len(item) == 2 else item
        full_query = getattr(query, "full_query", None)
        if not isinstance(full_query, str):
            continue
        if not getattr(query, "original_label", None):
            query.original_label = full_query
        query.full_query = normalizer.normalize(
            full_query, profile=profile
        ).normalized_text
        base_entity = getattr(query, "base_entity", None)
        if isinstance(base_entity, str):
            query.base_entity = normalizer.normalize(
                base_entity, profile=profile
            ).normalized_text
    return queries
