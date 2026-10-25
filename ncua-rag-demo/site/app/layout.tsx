import type { Metadata } from "next";
import "./globals.css";
import "./lab.css";

export const metadata: Metadata = {
  title: "Credit Union Evidence Lab",
  description: "Explore NCUA reports with cited evidence, LangChain, ChromaDB and Ollama.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
