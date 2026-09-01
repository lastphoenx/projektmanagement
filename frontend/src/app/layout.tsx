import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { getUiTheme } from "@/lib/uiTheme";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Projektmanagement",
  description: "Self-hosted Projektmanagement",
  applicationName: "Projektmanagement",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const uiTheme = getUiTheme();

  return (
    <html lang="de" data-ui-theme={uiTheme}>
      <body className={`${inter.variable} ${plusJakarta.variable} ${inter.className} antialiased`}>
        {children}
      </body>
    </html>
  );
}
