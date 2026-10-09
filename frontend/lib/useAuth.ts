"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, getMe, getToken, homeFor, logout, type Me, type Role } from "./api";

/**
 * Protège une page : redirige vers /login sans session valide,
 * ou vers le bon espace si le rôle ne correspond pas.
 */
export function useRequireAuth(role: Role) {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    getMe()
      .then((user) => {
        if (cancelled) return;
        if (user.role !== role) {
          router.replace(homeFor(user.role));
          return;
        }
        setMe(user);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          logout();
          router.replace("/login");
        } else {
          setError(err instanceof Error ? err.message : "Erreur inconnue");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [role, router]);

  const signOut = () => {
    logout();
    router.replace("/login?reason=logout");
  };

  return { me, error, signOut };
}
