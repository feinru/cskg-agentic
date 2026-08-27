"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";

interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
}

interface HistoryItem {
  id: string;
  date: string;
  preview: string;
  messages: Message[];
}

export default function History() {
  const router = useRouter();
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    // Load history from localStorage
    try {
      const historyStr = localStorage.getItem("cskg_chat_history");
      if (historyStr) {
        const historyObj = JSON.parse(historyStr) as Record<string, Omit<HistoryItem, "id">>;
        // Convert to array and sort by date descending
        const items: HistoryItem[] = Object.entries(historyObj)
          .map(([id, data]) => ({
            id,
            ...data
          }))
          .sort((a: HistoryItem, b: HistoryItem) => new Date(b.date).getTime() - new Date(a.date).getTime());
        
        setHistoryItems(items);
      }
    } catch (e) {
      console.error("Failed to load history", e);
    }
  }, []);

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const historyStr = localStorage.getItem("cskg_chat_history");
    if (historyStr) {
      const historyObj = JSON.parse(historyStr) as Record<string, Omit<HistoryItem, "id">>;
      delete historyObj[id];
      localStorage.setItem("cskg_chat_history", JSON.stringify(historyObj));
      window.dispatchEvent(new Event("historyUpdated"));
      
      const historyArray: HistoryItem[] = Object.keys(historyObj).map((key) => ({
        id: key,
        ...historyObj[key]
      })).sort((a: HistoryItem, b: HistoryItem) => new Date(b.date).getTime() - new Date(a.date).getTime());
      
      setHistoryItems(historyArray);
    }
  };

  const filteredHistory = historyItems.filter(item => 
    item.preview.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.messages.some((m: Message) => m.content.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className={styles.historyContainer}>
      <div className={styles.historyHeader}>
        <h1>Chat History</h1>
        <p style={{ color: 'var(--text-secondary)' }}>View your past investigations and queries.</p>
        
        <input 
          type="text"
          placeholder="Search history (titles and messages)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            marginTop: '1.5rem',
            width: '100%',
            maxWidth: '500px',
            padding: '0.75rem 1rem',
            border: '1px solid var(--border-dark)',
            borderRadius: '2px',
            fontFamily: 'inherit',
            fontSize: '0.95rem',
            backgroundColor: '#fff',
            color: '#202122'
          }}
        />
      </div>
      
      {filteredHistory.length === 0 ? (
        <div className={styles.emptyState}>
          <p>No chat history found. Start a new conversation!</p>
          <Link href="/">
            <button style={{ 
              background: '#f8f9fa', 
              color: '#202122', 
              border: '1px solid var(--border-dark)', 
              padding: '0.5rem 1rem', 
              fontFamily: 'inherit', 
              fontWeight: 500, 
              cursor: 'pointer', 
              marginTop: '1rem',
              borderRadius: '2px' 
            }}>
              Start New Chat
            </button>
          </Link>
        </div>
      ) : (
        <div className={styles.historyList}>
          {filteredHistory.map((item) => (
            <div 
              key={item.id} 
              className={styles.historyItem}
              onClick={() => router.push(`/?session=${item.id}`)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div className={styles.historyItemDate}>{formatDate(item.date)}</div>
                  <div className={styles.historyItemPreview}>{item.preview}</div>
                  <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    {item.messages.filter((m: Message) => m.role === 'user').length} queries
                  </div>
                </div>
                <button 
                  onClick={(e) => handleDelete(e, item.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '0.875rem'
                  }}
                >
                  [Del]
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
