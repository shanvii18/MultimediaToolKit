import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/shell/AppShell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MultimediaToolKit: convert text, images, audio, video and animation",
  description:
    "Twenty real conversions between text, images, audio, video and animation, with CPU engines and optional AI generation.",
};

// Applies the saved theme before first paint (no flash of the wrong theme).
const themeScript = `(function(){try{var t=localStorage.getItem("mtk_theme");if(!t){t=window.matchMedia("(prefers-color-scheme: light)").matches?"light":"dark"}var c=document.documentElement.classList;c.remove("dark","light");c.add(t)}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={inter.className}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
