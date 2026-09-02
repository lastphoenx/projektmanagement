import { PLANNING_IDEA, type PlanningStepKey } from "@/lib/planning-steps";

/** Artefakt-Slugs mit KI-Generierung (Schritte 1–6, 9–10). */
export const KI_GENERATABLE_ARTIFACT_SLUGS = [
  "zielplanung",
  "projektbeschrieb",
  "psp",
  "pflichtenheft",
  "netzplan",
  "projektplan",
  "einsatzmittelplan",
  "risikobetrachtung",
] as const;

/** Artefakt-Slugs mit deterministischer PSP-Generierung. */
export const PSP_GENERATABLE_ARTIFACT_SLUGS = ["jira_csv", "budgetplan"] as const;

export function canGenerateKi(step: PlanningStepKey): boolean {
  if (step === PLANNING_IDEA.key) return true;
  return (KI_GENERATABLE_ARTIFACT_SLUGS as readonly string[]).includes(step);
}

export function canGenerateFromPsp(step: PlanningStepKey): boolean {
  return (PSP_GENERATABLE_ARTIFACT_SLUGS as readonly string[]).includes(step);
}
