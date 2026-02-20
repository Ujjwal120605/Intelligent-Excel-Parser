import type { Metadata } from "next";
import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const robotoMono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LATSPACE AI",
  description: "Intelligent Data Parsing System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${robotoMono.variable} antialiased bg-[#f8f9fa] min-h-screen p-4 md:p-8 flex items-center justify-center`}
      >
        <main className="w-full max-w-5xl bg-white brutal-border brutal-shadow min-h-[80vh] flex flex-col relative overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
