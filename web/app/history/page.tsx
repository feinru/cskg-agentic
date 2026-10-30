"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { HistoryItem, Message } from "./types";
import { HistoryList } from "./list";

export default function HistoryPage() {
  const router = useRouter();
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    try {
      const historyStr = localStorage.getItem("cskg_chat_history");
      if (historyStr) {
        const historyObj = JSON.parse(historyStr) as Record<string, Omit<HistoryItem, "id">>;
        const items = Object.entries(historyObj)
          .map(([id, data]) => ({ id, ...data }))
          .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        setHistoryItems(items);
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const historyStr = localStorage.getItem("cskg_chat_history");
    if (historyStr) {
      const historyObj = JSON.parse(historyStr);
      delete historyObj[id];
      localStorage.setItem("cskg_chat_history", JSON.stringify(historyObj));
      window.dispatchEvent(new Event("historyUpdated"));
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
    }
  };

  const filteredHistory = historyItems.filter(
    (item) =>
      item.preview.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.messages.some((m: Message) => m.content.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className={styles.historyContainer}>
      <div className={styles.historyHeader}>
        <h1>Chat History</h1>
        <p style={{ color: "var(--text-secondary)" }}>View your past investigations and queries.</p>
        <input
          type="text"
          placeholder="Search history..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            marginTop: "1.5rem",
            width: "100%",
            maxWidth: "500px",
            padding: "0.75rem 1rem",
            border: "1px solid var(--border-dark)",
            borderRadius: "2px",
            fontFamily: "inherit",
            fontSize: "0.95rem",
          }}
        />
      </div>

      {filteredHistory.length === 0 ? (
        <div className={styles.emptyState}>
          <p>No chat history found. Start a new conversation!</p>
          <Link href="/">
            <button
              type="button"
              style={{
                background: "#f8f9fa",
                border: "1px solid var(--border-dark)",
                padding: "0.5rem 1rem",
                marginTop: "1rem",
                cursor: "pointer",
                borderRadius: "2px",
              }}
            >
              Start New Chat
            </button>
          </Link>
        </div>
      ) : (
        <HistoryList
          items={filteredHistory}
          onSelect={(id) => router.push(`/?session=${id}`)}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}
