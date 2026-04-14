import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "./components/Sidebar";
import AuthGuard from "./components/AuthGuard";

export const metadata: Metadata = {
  title: "AI Ad Factory",
  description: "Generate AI-powered ads",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex bg-gray-950 text-white min-h-screen">
        <AuthGuard>
          <Sidebar />
          <main className="flex-1 p-8 overflow-y-auto">
            {children}
          </main>
        </AuthGuard>
      </body>
    </html>
  );
}
