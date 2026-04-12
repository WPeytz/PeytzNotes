import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PeytzNotes",
  description: "Search and chat with your university notes",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="bg-gray-950 text-gray-100 min-h-full flex flex-col">
        <nav className="border-b border-gray-800 px-6 py-4">
          <div className="max-w-4xl mx-auto flex items-center gap-6">
            <a href="/" className="text-lg font-semibold">
              PeytzNotes
            </a>
            <a href="/" className="text-sm text-gray-400 hover:text-white">
              Chat
            </a>
            <a href="/notes" className="text-sm text-gray-400 hover:text-white">
              Notes
            </a>
            <a href="/search" className="text-sm text-gray-400 hover:text-white">
              Search
            </a>
            <a href="/study" className="text-sm text-gray-400 hover:text-white">
              Study
            </a>
            <a
              href="/course/deep-learning-cv"
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              DL in CV
            </a>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto w-full px-6 py-8 flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}
