import type { Metadata } from "next";

export const metadata: Metadata = {
  title:       "Codebase Memory Engine",
  description: "Ask questions about any codebase in plain English",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}