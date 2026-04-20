import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "VisagePass — Professional Passport & Visa Photos",
  description:
    "Create compliant passport and visa photos for 50+ countries. AI-powered background removal, face detection, and 300 DPI print-ready output.",
  keywords:
    "passport photo online, visa photo editor, biometric passport photo, ID photo maker",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
