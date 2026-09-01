/** KI-Projektplanungsschritte — Idee + 10 Artefakte */

import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  ArrowRightLeft,
  CalendarDays,
  ClipboardList,
  FileText,
  GitBranch,
  Lightbulb,
  Network,
  Target,
  Users,
  Wallet,
} from "lucide-react";

export const PLANNING_IDEA = {
  key: "project_idea",
  number: 0,
  label: "Projektidee",
  shortLabel: "Idee",
  description: "Ausgangslage und Vision — der Startpunkt jeder Planung.",
  icon: Lightbulb,
} as const;

export const PLANNING_ARTIFACTS: ReadonlyArray<{
  key: string;
  number: number;
  label: string;
  shortLabel: string;
  description: string;
  icon: LucideIcon;
}> = [
  {
    key: "zielplanung",
    number: 1,
    label: "Zielplanung",
    shortLabel: "Ziele",
    description: "SMART-Ziele und Erfolgskriterien definieren.",
    icon: Target,
  },
  {
    key: "projektbeschrieb",
    number: 2,
    label: "Projektbeschrieb",
    shortLabel: "Beschrieb",
    description: "Rahmen, Scope und Kontext dokumentieren.",
    icon: FileText,
  },
  {
    key: "psp",
    number: 3,
    label: "Projektstrukturplan",
    shortLabel: "PSP",
    description: "Arbeitspakete und Hierarchie strukturieren.",
    icon: Network,
  },
  {
    key: "pflichtenheft",
    number: 4,
    label: "Pflichtenheft (kurz)",
    shortLabel: "Pflichtenheft",
    description: "Anforderungsbasis fürs Projektsetup.",
    icon: ClipboardList,
  },
  {
    key: "netzplan",
    number: 5,
    label: "Netzplan",
    shortLabel: "Netzplan",
    description: "Abhängigkeiten und kritischen Pfad planen.",
    icon: GitBranch,
  },
  {
    key: "projektplan",
    number: 6,
    label: "Projektplan (Gantt)",
    shortLabel: "Gantt",
    description: "Termine, Meilensteine und Zeitachse.",
    icon: CalendarDays,
  },
  {
    key: "jira_csv",
    number: 7,
    label: "Jira CSV",
    shortLabel: "Jira",
    description: "Jira-Import-CSV aus dem PSP.",
    icon: ArrowRightLeft,
  },
  {
    key: "budgetplan",
    number: 8,
    label: "Budgetplan",
    shortLabel: "Budget",
    description: "Kosten und Finanzplanung je Arbeitspaket.",
    icon: Wallet,
  },
  {
    key: "einsatzmittelplan",
    number: 9,
    label: "Einsatzmittelplan",
    shortLabel: "Ressourcen",
    description: "Rollen, Kapazitäten und Einsatz planen.",
    icon: Users,
  },
  {
    key: "risikobetrachtung",
    number: 10,
    label: "Risikobetrachtung",
    shortLabel: "Risiko",
    description: "Risiken identifizieren und bewerten.",
    icon: AlertTriangle,
  },
];

export type PlanningStepKey = typeof PLANNING_IDEA.key | (typeof PLANNING_ARTIFACTS)[number]["key"];

export const PLANNING_STEP_COUNT = PLANNING_ARTIFACTS.length;

export interface PlanningFlowStep {
  key: PlanningStepKey;
  displayNumber: number;
  label: string;
  shortLabel: string;
  description: string;
  icon: LucideIcon;
  kind: "idea" | "artifact";
}

export const PLANNING_FLOW_STEPS: PlanningFlowStep[] = [
  {
    key: PLANNING_IDEA.key,
    displayNumber: 1,
    label: PLANNING_IDEA.label,
    shortLabel: PLANNING_IDEA.shortLabel,
    description: PLANNING_IDEA.description,
    icon: PLANNING_IDEA.icon,
    kind: "idea",
  },
  ...PLANNING_ARTIFACTS.map((artifact) => ({
    key: artifact.key as PlanningStepKey,
    displayNumber: artifact.number + 1,
    label: artifact.label,
    shortLabel: artifact.shortLabel,
    description: artifact.description,
    icon: artifact.icon,
    kind: "artifact" as const,
  })),
];

export const STATUS_LABELS: Record<string, string> = {
  pending: "Offen",
  draft: "Entwurf",
  approved: "Freigegeben",
};
