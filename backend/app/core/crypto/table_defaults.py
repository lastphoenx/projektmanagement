"""Tabellen-Defaults für classification — aus SQLAlchemy-Models abgeleitet (Single Source of Truth)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from sqlalchemy.orm import DeclarativeBase

from app.core.crypto.classification import DataClassification


@dataclass(frozen=True, slots=True)
class TableClassificationDefault:
    model: str
    table: str
    default_classification: str
    default_level: int


def _classification_from_column_default(default_arg) -> DataClassification:
    if isinstance(default_arg, DataClassification):
        return default_arg
    if isinstance(default_arg, int):
        return DataClassification(default_arg)
    raise TypeError(f"Unsupported classification default: {default_arg!r}")


def _iter_classified_mappers(base: Type[DeclarativeBase]):
    for mapper in base.registry.mappers:
        if "classification" in mapper.columns:
            yield mapper


def discover_table_classification_defaults(
    base: Type[DeclarativeBase],
) -> list[TableClassificationDefault]:
    """Alle Models mit classification-Spalte — Default aus Column-Metadata."""
    rows: list[TableClassificationDefault] = []
    for mapper in _iter_classified_mappers(base):
        col = mapper.columns["classification"]
        if col.default is None or col.default.arg is None:
            continue
        level = _classification_from_column_default(col.default.arg)
        rows.append(
            TableClassificationDefault(
                model=mapper.class_.__name__,
                table=mapper.local_table.name,
                default_classification=level.name,
                default_level=int(level),
            )
        )
    return sorted(rows, key=lambda r: r.model)


def table_defaults_as_dicts(base: Type[DeclarativeBase]) -> list[dict]:
    return [
        {
            "model": row.model,
            "table": row.table,
            "default_classification": row.default_classification,
            "policy_source": "sqlalchemy_model",
        }
        for row in discover_table_classification_defaults(base)
    ]


def table_default_name_for_model(base: Type[DeclarativeBase], model_name: str) -> str | None:
    for row in discover_table_classification_defaults(base):
        if row.model == model_name:
            return row.default_classification
    return None
