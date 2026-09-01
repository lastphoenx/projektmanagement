export type WizardProjectType =
  | "new_product"
  | "process_improvement"
  | "infrastructure"
  | "other";

export const WIZARD_PROJECT_TYPE_LABELS: Record<WizardProjectType, string> = {
  new_product: "Neues Produkt / Feature",
  process_improvement: "Prozess-Verbesserung",
  infrastructure: "Infrastruktur",
  other: "Sonstiges",
};

export const WIZARD_PROJECT_TYPES = Object.keys(
  WIZARD_PROJECT_TYPE_LABELS
) as WizardProjectType[];
