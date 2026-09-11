"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { getAccessToken, isPreviewAutoLoginEnabled, tryPreviewAutoLogin } from "../lib/auth";

export function PreviewAutoLogin() {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!isPreviewAutoLoginEnabled() || !["/", "/login"].includes(pathname)) return;
    let cancelled = false;
    void (getAccessToken() ? Promise.resolve(true) : tryPreviewAutoLogin()).then((ready) => {
      if (ready && !cancelled) router.replace("/dashboard");
    });
    return () => { cancelled = true; };
  }, [pathname, router]);

  return null;
}
