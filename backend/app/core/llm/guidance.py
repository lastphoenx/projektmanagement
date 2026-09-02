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
                "Grosse Modelle (z. B. 70B) brauchen viel RAM/VRAM auf dem Ollama-Host.",
                "Nur Chat-taugliche Modelle erscheinen in der Liste.",
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
            "ollama": "llama3.3:70b, llama3:8b",
            "openai": "gpt-4o-mini, gpt-4.1-mini",
            "anthropic": "claude-haiku-4-5",
        },
        {
            "use_case": "Ausformulierte Planungstexte",
            "ollama": "llama3.3:70b, qwen2.5:32b",
            "openai": "gpt-4.1",
            "anthropic": "claude-sonnet-5",
        },
        {
            "use_case": "Tabellen / PSP-Struktur (Schritt 3)",
            "ollama": "llama3.3:70b, qwen2.5:32b",
            "openai": "gpt-4.1-mini",
            "anthropic": "claude-sonnet-5",
        },
    ],
    "ollama_filter_note": (
        "Embedding-, Vision- (…vl), Reranker- und reine Code-Modelle werden ausgeblendet — "
        "sie eignen sich nicht für Planungs-Texte."
    ),
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
