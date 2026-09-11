import type { Metadata } from "next";
import "./globals.css";
import { PreviewAutoLogin } from "../components/PreviewAutoLogin";

export const metadata: Metadata = {
  title: "PaperForge | Verified Academic Document Agent",
  description: "PaperForge is a verified agent system for academic document review, controlled transformation, provenance tracking and DOCX verification.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body><PreviewAutoLogin />{children}</body>
    </html>
  );
}
