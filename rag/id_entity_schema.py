"""Pydantic contracts for Indonesian clinical entity extraction (Stage 2)."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SourceField(str, Enum):
    QUESTION = "question"
    ANSWER = "answer"


class Speaker(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"


class EntityType(str, Enum):
    CONDITION = "condition"
    SYMPTOM = "symptom"
    CLINICAL_FINDING = "clinical_finding"
    MEASUREMENT = "measurement"
    DRUG = "drug"
    PROCEDURE = "procedure"
    ANATOMY = "anatomy"
    DEMOGRAPHIC = "demographic"
    UNIT = "unit"
    VISIT = "visit"
    OTHER = "other"


class ClinicalDomain(str, Enum):
    CONDITION = "condition"
    MEASUREMENT = "measurement"
    OBSERVATION = "observation"
    DRUG = "drug"
    PROCEDURE = "procedure"
    UNIT = "unit"
    VISIT = "visit"
    ALL = "all"


class Assertion(str, Enum):
    PRESENT = "present"
    NEGATED = "negated"
    UNCERTAIN = "uncertain"
    HYPOTHETICAL = "hypothetical"


class Temporal(str, Enum):
    PRESENT = "present"
    PAST = "past"
    FUTURE = "future"
    UNKNOWN = "unknown"


class Experiencer(str, Enum):
    PATIENT = "patient"
    FAMILY = "family"
    OTHER = "other"
    UNKNOWN = "unknown"


class EpistemicStatus(str, Enum):
    PATIENT_FACT = "patient_fact"
    DIFFERENTIAL_DIAGNOSIS = "differential_diagnosis"
    GENERAL_INFORMATION = "general_information"
    RECOMMENDED = "recommended"
    CONDITIONAL = "conditional"
    HYPOTHETICAL = "hypothetical"
    UNKNOWN = "unknown"


class ProvenanceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_index: int = Field(ge=1)
    stage: NonEmptyString
    raw_text_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    normalized_text_sha256: Annotated[
        str, StringConstraints(pattern=r"^[0-9a-f]{64}$")
    ]


class Stage2InputDocument(BaseModel):
    """Contract produced by Milestone A Checkpoint 1."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    document_id: NonEmptyString
    parent_record_id: NonEmptyString
    source_field: SourceField
    speaker: Speaker
    raw_text: NonEmptyString
    normalized_text: NonEmptyString
    sentences: list[NonEmptyString] = Field(min_length=1)
    sentence_count: int = Field(ge=1)
    source: NonEmptyString
    url: NonEmptyString
    title: NonEmptyString
    normalization_profile: SourceField
    normalizer_version: NonEmptyString
    resource_version: NonEmptyString
    normalization_warnings: list[str] = Field(default_factory=list)
    provenance: ProvenanceModel
    schema_version: NonEmptyString

    @model_validator(mode="after")
    def validate_input_contract(self) -> "Stage2InputDocument":
        expected_speaker = {
            SourceField.QUESTION: Speaker.PATIENT,
            SourceField.ANSWER: Speaker.DOCTOR,
        }[SourceField(self.source_field)]
        if Speaker(self.speaker) != expected_speaker:
            raise ValueError(
                f"speaker must be '{expected_speaker.value}' for "
                f"source_field '{self.source_field}'"
            )
        if SourceField(self.normalization_profile) != SourceField(self.source_field):
            raise ValueError("normalization_profile must match source_field")
        if self.sentence_count != len(self.sentences):
            raise ValueError("sentence_count must equal len(sentences)")
        expected_document_id = f"{self.parent_record_id}-{self.source_field}"
        if self.document_id != expected_document_id:
            raise ValueError(
                f"document_id must be '{expected_document_id}' for this document"
            )
        cursor = 0
        for sentence in self.sentences:
            position = self.normalized_text.find(sentence, cursor)
            if position < 0:
                raise ValueError(
                    "sentences must occur in source order in normalized_text"
                )
            cursor = position + len(sentence)
        return self


class ClinicalEntity(BaseModel):
    """One auditable clinical entity mention."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    entity_id: NonEmptyString
    mention: NonEmptyString
    normalized_mention: NonEmptyString
    base_entity: NonEmptyString
    entity_type: EntityType
    domain: ClinicalDomain
    associated_entities: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    value: int | float | str | None = None
    unit: str | None = None
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    method: str | None = None
    visit: str | None = None
    assertion: Assertion
    temporal: Temporal
    temporal_expression: str | None = None
    experiencer: Experiencer
    epistemic_status: EpistemicStatus
    source_field: SourceField
    speaker: Speaker
    sentence_id: int = Field(ge=0)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    evidence: NonEmptyString
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_entity_fields(self) -> "ClinicalEntity":
        if self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        expected_speaker = {
            SourceField.QUESTION: Speaker.PATIENT,
            SourceField.ANSWER: Speaker.DOCTOR,
        }[SourceField(self.source_field)]
        if Speaker(self.speaker) != expected_speaker:
            raise ValueError(
                f"speaker must be '{expected_speaker.value}' for "
                f"source_field '{self.source_field}'"
            )
        if self.mention not in self.evidence:
            raise ValueError("mention must occur in evidence")
        return self


class ClinicalExtractionDocument(BaseModel):
    """Validated extraction result for one Stage 2 input document."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    document_id: NonEmptyString
    parent_record_id: NonEmptyString
    source_field: SourceField
    speaker: Speaker
    normalized_text: NonEmptyString
    sentences: list[NonEmptyString] = Field(min_length=1)
    entities: list[ClinicalEntity] = Field(default_factory=list)
    schema_version: NonEmptyString = "1.0.0"

    @model_validator(mode="after")
    def validate_document_and_entities(self) -> "ClinicalExtractionDocument":
        expected_speaker = {
            SourceField.QUESTION: Speaker.PATIENT,
            SourceField.ANSWER: Speaker.DOCTOR,
        }[SourceField(self.source_field)]
        if Speaker(self.speaker) != expected_speaker:
            raise ValueError(
                f"speaker must be '{expected_speaker.value}' for "
                f"source_field '{self.source_field}'"
            )
        expected_document_id = f"{self.parent_record_id}-{self.source_field}"
        if self.document_id != expected_document_id:
            raise ValueError(
                f"document_id must be '{expected_document_id}' for this document"
            )

        entity_ids: set[str] = set()
        for entity in self.entities:
            if entity.entity_id in entity_ids:
                raise ValueError(f"duplicate entity_id: {entity.entity_id}")
            entity_ids.add(entity.entity_id)
            if SourceField(entity.source_field) != SourceField(self.source_field):
                raise ValueError("entity source_field must match document source_field")
            if Speaker(entity.speaker) != Speaker(self.speaker):
                raise ValueError("entity speaker must match document speaker")
            if entity.sentence_id >= len(self.sentences):
                raise ValueError("entity sentence_id is outside sentences")
            if entity.end_char > len(self.normalized_text):
                raise ValueError("entity end_char is outside normalized_text")
            span = self.normalized_text[entity.start_char : entity.end_char]
            if span != entity.mention:
                raise ValueError(
                    f"mention-offset mismatch: expected '{span}', "
                    f"received '{entity.mention}'"
                )
            sentence = self.sentences[entity.sentence_id]
            if entity.evidence not in sentence:
                raise ValueError("entity evidence must occur in its sentence")
        return self
