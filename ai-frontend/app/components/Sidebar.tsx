"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getSupabase } from "../../lib/supabase";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  if (pathname === "/login") return null;

  const links = [
    { href: "/", label: "Generate" },
    { href: "/history", label: "History" },
    { href: "/analytics", label: "Analytics" },
  ];

  async function handleSignOut() {
    const sb = getSupabase();
    await sb.auth.signOut();
    router.push("/login");
  }

  return (
    <aside className="w-56 min-h-screen bg-gray-900 text-white flex flex-col p-4">
      <div className="text-xl font-bold mb-6 px-2">TikTok Affiliate AI</div>

      <div className="flex flex-col gap-2 flex-1">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`px-3 py-2 rounded-lg transition-colors ${
              pathname === link.href
                ? "bg-pink-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </div>

      <button
        onClick={handleSignOut}
        className="mt-auto px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors text-left"
      >
        Sign Out
      </button>
    </aside>
  );
}
