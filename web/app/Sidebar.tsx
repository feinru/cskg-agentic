"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import styles from "./layout.module.css";

interface HistoryItem {
  id: string;
  preview: string;
  date: string;
}

export default function Sidebar() {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    const loadHistory = () => {
      try {
        const historyStr = localStorage.getItem("cskg_chat_history");
        if (historyStr) {
          const historyObj = JSON.parse(historyStr);
          const historyArray = Object.keys(historyObj).map((key) => ({
            id: key,
            preview: historyObj[key].preview,
            date: historyObj[key].date,
          })).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
          setHistoryItems(historyArray);
        } else {
          setHistoryItems([]);
        }
      } catch (e) {
        console.error("Failed to load history for sidebar", e);
      }
    };

    // Load initially
    loadHistory();

    // Listen for storage changes from other tabs/actions
    window.addEventListener("storage", loadHistory);

    // Custom event for same-tab updates
    window.addEventListener("historyUpdated", loadHistory);

    return () => {
      window.removeEventListener("storage", loadHistory);
      window.removeEventListener("historyUpdated", loadHistory);
    };
  }, []);

  return (
    <aside className={`${styles.sidebar} ${isCollapsed ? styles.sidebarCollapsed : ''}`}>
      {!isCollapsed && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className={styles.sidebarTitle} style={{ justifyContent: 'space-between' }}>
            <span>Chat CSKG</span>
            <button 
              onClick={() => setIsCollapsed(true)}
              className={styles.collapseButton}
              title="Collapse Sidebar"
            >
              [«]
            </button>
          </div>
          <nav>
            <Link href="/" className={styles.navLink}>
              [New Chat]
            </Link>
            <Link href="/history" className={styles.navLink}>
              [History]
            </Link>

            <div className={styles.sidebarHistoryList}>
              {historyItems.slice(0, 10).map((item) => (
                <Link key={item.id} href={`/?session=${item.id}`} className={styles.sidebarHistoryItem}>
                  [{item.preview}]
                </Link>
              ))}
            </div>
          </nav>
          
          <div className={styles.sidebarLicense} style={{ marginTop: 'auto' }}>
            <p>Fein - GNU AGPLv3 © {new Date().getFullYear()}</p>
          </div>
        </div>
      )}

      {isCollapsed && (
        <button 
          onClick={() => setIsCollapsed(false)}
          className={styles.collapseButtonCollapsed}
          title="Expand Sidebar"
        >
          [»]
        </button>
      )}
    </aside>
  );
}
