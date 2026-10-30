"use client";

import styles from "./page.module.css";
import { HistoryItem, Message } from "./types";

interface HistoryListProps {
  items: HistoryItem[];
  onSelect: (id: string) => void;
  onDelete: (e: React.MouseEvent, id: string) => void;
}

export function HistoryList({ items, onSelect, onDelete }: HistoryListProps) {
  const formatDate = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={styles.historyList}>
      {items.map((item) => (
        <div key={item.id} className={styles.historyItem} onClick={() => onSelect(item.id)}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div className={styles.historyItemDate}>{formatDate(item.date)}</div>
              <div className={styles.historyItemPreview}>{item.preview}</div>
              <div style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                {item.messages.filter((m: Message) => m.role === "user").length} queries
              </div>
            </div>
            <button
              type="button"
              onClick={(e) => onDelete(e, item.id)}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-secondary)",
                cursor: "pointer",
                fontSize: "0.85rem",
              }}
            >
              [Del]
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
