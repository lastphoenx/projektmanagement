"""Statische KI-Hilfetexte für die Benutzer-Einstellungsseite."""

GUIDANCE = {
    "controls": {
        "title": "Was Sie hier steuern",
        "items": [
            "Welcher KI-Anbieter für Ihre Planungs-Generierung genutzt wird (Idee, Artefakte).",
            "Welches Modell innerhalb des Anbieters verwendet wird.",
            "API-Keys und Server-Adressen legt der Betreiber in der Server-.env fest — nicht hier.",
        ],
    },
    "providers": [
        {
            "id": "ollama",
            "pros": [
                "Daten bleiben im Haus (kein Cloud-Versand).",
                "Keine API-Kosten pro Request.",
                "Geeignet für vertrauliche Planungsinhalte ohne Anonymisierung.",
            ],
            "cons": [
                "Qualität hängt vom lokalen Modell und der Hardware ab.",
                "Muss vom Betreiber erreichbar gehalten werden.",
            ],
        },
        {
            "id": "openai",
            "pros": [
                "Hohe Textqualität, schnelle Antworten.",
                "Breite Modellauswahl (gpt-4o-mini für Entwürfe, gpt-4o für Qualität).",
            ],
            "cons": [
                "Text wird an OpenAI gesendet (nach Anonymisierung, siehe Datenschutz).",
                "Laufende API-Kosten.",
            ],
        },
        {
            "id": "anthropic",
            "pros": [
                "Sehr gute Qualität bei langen, strukturierten Texten.",
                "Claude Haiku für schnelle Entwürfe, Sonnet für anspruchsvolle Planung.",
            ],
            "cons": [
                "Text wird an Anthropic gesendet (nach Anonymisierung).",
                "Laufende API-Kosten; Anbindung kann vom Betreiber noch eingeschränkt sein.",
            ],
        },
    ],
    "model_hints": [
        {
            "use_case": "Schnelle Entwürfe (Idee, Stichpunkte)",
            "ollama": "llama3.2, mistral",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-latest",
        },
        {
            "use_case": "Ausformulierte Planungstexte",
            "ollama": "llama3.1, qwen2.5",
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-0",
        },
        {
            "use_case": "Tabellen/PSP-Struktur (Schritt 3)",
            "ollama": "Modell mit guter Markdown-Treue testen",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-0",
        },
    ],
    "privacy": {
        "title": "Datenschutz bei Cloud-KI",
        "rules": [
            "SECRET-Klassifizierung: Versand an externe KI ist blockiert.",
            "INTERNAL und CONFIDENTIAL: Text wird vor dem Versand automatisch anonymisiert (PII-Gate).",
            "PUBLIC: unverändert — nur für unkritische Inhalte geeignet.",
            "Lokal (Ollama): kein PII-Gate nötig — Daten verlassen die Infrastruktur nicht.",
        ],
        "note": "Die Anonymisierung ersetzt keine fachliche Prüfung. Prüfen Sie generierte Texte vor Freigabe.",
    },
}
