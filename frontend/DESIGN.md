# UI-Leitplanken — Projektmanagement

Verbindlich für alle neuen und überarbeiteten Oberflächen. Referenz: pm-suite (Klarheit, Statusfarben), eigenes Layout (Sidebar, Chrome).

## 1. Farb-Semantik (nicht dekorativ)

| Bedeutung | Farbe | Verwendung |
|-----------|-------|------------|
| **Aktiv / Navigation** | Blau (`primary`) | Ausgewählter Sidebar-Eintrag, primäre CTAs |
| **Offen / ausstehend** | Gelb/Amber | Planungsschritt-**Icon** ohne Inhalt |
| **Erledigt / Inhalt** | Grün/Emerald | Planungsschritt-**Icon** mit Inhalt |
| **Entwurf** | Amber-Badge | Status «Entwurf» am Dokument |
| **Freigegeben** | Grün-Badge | Status «Freigegeben» |
| **Bearbeitung** | Grün-Banner | «Du bearbeitest …» — nur im Edit-Modus |
| **Fehler** | Rot (`destructive`) | API-Fehler, Validierung |
| **KI** | Sekundär / Outline | KI-Aktionen, nie primär-blau |

**Regel:** Gelb/Grün nur an den **Schritt-Icons** (Badge), nicht die ganze Zeile einfärben. Zeilen-Auswahl bleibt blau.

## 2. Planungs-Editor — kein permanenter Split

**Entscheidung:** Der dauerhafte Zwei-Spalten-Editor (Bearbeiten | Vorschau) verbraucht zu viel Platz und verwässert den Lesemodus.

### Modi

1. **Lesemodus (Standard)** — volle Breite, Inhalt als lesbare Fläche (`planning-read-panel`).
2. **Bearbeitungsmodus** — Button «Bearbeiten»; grüner Banner; **ein** Editor in voller Breite (`planning-editor-field`).
3. **Vorschau (optional)** — Toggle «Vorschau» nur im Bearbeitungsmodus; Split ab `lg`, sonst Tab-Wechsel Editor ↔ Vorschau.

Beim Schrittwechsel: zurück in den **Lesemodus**.

## 3. Layout & Komponenten

- **Chrome:** Dunkle Kopf-/Fussleiste (`app-chrome`), helle Inhaltsfläche (`app-page-bg`).
- **Karten:** `rounded-2xl`, `shadow-card`, `border-border/70`.
- **Seiten:** `PageContainer` + `PageHeader`; Zurück-Link einheitlich mit Pfeil.
- **Fehler:** `InlineAlert` (rot), nie nur Rohtext.
- **Status:** `StatusBadge` für pending / draft / approved.

Wiederverwendbare Bausteine unter `src/components/planning/` und `src/components/ui/`.

## 4. Button-Hierarchie

| Stufe | Stil | Beispiel |
|-------|------|----------|
| Primär | `Button` default | Speichern, Anmelden |
| Sekundär | `variant="secondary"` | KI generieren, Aus PSP generieren |
| Tertiär | `variant="outline"` | Als Entwurf, Abbrechen |
| Ghost | `variant="ghost"` | Icon-Buttons (Stift, Löschen) |

Max. **ein** primärer Button pro Aktionsgruppe.

## 5. Typografie

- Überschriften: `font-display`, `tracking-tight`.
- Projekt-Key: `font-mono`, `text-xs`, muted.
- Editor: `font-mono`, `text-sm`, `leading-relaxed`.
- Labels: `text-xs uppercase tracking-wide text-muted-foreground`.

## 6. Prozess für neue Features

1. Leitplanken prüfen (dieses Dokument).
2. Bestehende Komponenten nutzen, keine Ad-hoc-Styles in Pages.
3. Kein neues Farbschema pro Screen.
4. UI-Tuning in eigenem Schritt, nicht vermischt mit Backend-Logik.

## 7. Bewusst später (nicht jetzt)

- Markdown-Rendering (nur Preformatted-Text in Vorschau).
- Live-Vorschau mit Syntax-Highlighting.
- Vollständiger pm-suite-Framework-Screen (2000 Zeilen).
- Theme-Switch / `data-ui-theme="km"` produktiv aktivieren.
