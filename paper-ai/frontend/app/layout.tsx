import type { Metadata } from "next";
import "./globals.css";
import { PreviewAutoLogin } from "../components/PreviewAutoLogin";

export const metadata: Metadata = {
  title: "PaperForge | Verified Academic Document Agent",
  description: "PaperForge is a verified academic document workflow for processing papers, parsing templates, verifying changes and generating reviewable reports.",
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
