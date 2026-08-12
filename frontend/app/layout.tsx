import "./globals.css";

export const metadata = {
  title: "Message Intelligence",
  description: "Privacy-first AI message classification, task extraction, and sensitive data detection"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
