"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Legacy-Route — KI-Einstellungen sind pro Benutzer unter /settings/llm. */
export default function AdminLlmRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/settings/llm");
  }, [router]);
  return null;
}
