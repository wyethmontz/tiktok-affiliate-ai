"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getSupabase } from "../../lib/supabase";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const sb = getSupabase();

    const checkSession = async () => {
      const { data } = await sb.auth.getSession();
      if (data.session) {
        setAuthenticated(true);
      } else if (pathname !== "/login") {
        router.push("/login");
      }
      setLoading(false);
    };

    checkSession();

    const { data: listener } = sb.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setAuthenticated(true);
      } else {
        setAuthenticated(false);
        if (pathname !== "/login") {
          router.push("/login");
        }
      }
    });

    return () => listener.subscription.unsubscribe();
  }, [router, pathname]);

  if (pathname === "/login") {
    return <>{children}</>;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
        Loading...
      </div>
    );
  }

  if (!authenticated) {
    return null;
  }

  return <>{children}</>;
}
