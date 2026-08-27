import type { Metadata } from "next";
import "./globals.css";
import styles from "./layout.module.css";
import Sidebar from "./Sidebar";

export const metadata: Metadata = {
  title: "Chat CSKG",
  description: "Cybersecurity Knowledge Graph Chatbot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>
        <div className={styles.appContainer}>
          <Sidebar />
          <main className={styles.mainContent}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
