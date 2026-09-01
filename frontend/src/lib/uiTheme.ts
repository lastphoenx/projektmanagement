export type UiTheme = "legacy" | "km";

export function getUiTheme(): UiTheme {
  const raw = process.env.NEXT_PUBLIC_UI_THEME?.trim().toLowerCase();
  if (raw === "legacy") return "legacy";
  return "km";
}
