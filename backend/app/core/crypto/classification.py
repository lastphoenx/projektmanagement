"""Datenklassifizierung gemäss Schutzklassen-Modell."""

from enum import IntEnum


class DataClassification(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    SECRET = 3

    @property
    def requires_master_key(self) -> bool:
        return self in (DataClassification.INTERNAL, DataClassification.CONFIDENTIAL)

    @property
    def requires_user_key(self) -> bool:
        return self == DataClassification.SECRET

    @property
    def requires_anonymization_before_external_llm(self) -> bool:
        return self in (
            DataClassification.INTERNAL,
            DataClassification.CONFIDENTIAL,
            DataClassification.SECRET,
        )

    @property
    def never_leaves_infrastructure(self) -> bool:
        return self == DataClassification.SECRET


def classification_label(value: int) -> str:
    return DataClassification(value).name
