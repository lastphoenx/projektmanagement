#!/usr/bin/env python3
"""Lädt spaCy + Flair-Modelle für swiss-pii-anonymizer (Server-Vorbereitung)."""

from __future__ import annotations


def main() -> None:
    from swiss_pii_anonymizer import anonymize

    sample = "Kontakt: Maria Muster, AHV 756.1234.5678.97"
    result = anonymize(sample)
    print(f"OK — {len(result.findings)} Fundstelle(n), Text-Länge {len(result.text)}")


if __name__ == "__main__":
    main()
