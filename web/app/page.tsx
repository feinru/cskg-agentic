"use client";
import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import ReactMarkdown from 'react-markdown';
import styles from "./page.module.css";

interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
}

export default function Home() {
  return (
    <Suspense fallback={<div style={{ padding: '2rem' }}>Loading...</div>}>
      <ChatApp />
    </Suspense>
  );
}

function ChatApp() {
  const searchParams = useSearchParams();
  const sessionParam = searchParams.get('session');

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionParam) {
      try {
        const historyStr = localStorage.getItem("cskg_chat_history");
        if (historyStr) {
          const historyObj = JSON.parse(historyStr);
          if (historyObj[sessionParam]) {
            setSessionId(sessionParam);
            setMessages(historyObj[sessionParam].messages);
            return;
          }
        }
      } catch (e) {
        console.error("Failed to load session from history", e);
      }
    }

    // Start a new session
    setSessionId(uuidv4());
    
    // Add initial greeting
    setMessages([
      {
        id: uuidv4(),
        role: "agent",
        content: "Hello! I am your CSKG SOC Analyst Agent. How can I help you investigate security threats today?"
      }
    ]);
  }, [sessionParam]);

  const saveToHistory = (newMessages) => {
    try {
      const historyStr = localStorage.getItem("cskg_chat_history");
      let history = historyStr ? JSON.parse(historyStr) : {};

      // Don't save if there are only initial greeting messages
      if (newMessages.length <= 1) return;

      const userMsg = newMessages.find((m: Message) => m.role === 'user');

      history[sessionId] = {
        date: new Date().toISOString(),
        preview: userMsg ? userMsg.content : "New Chat",
        messages: newMessages
      };

      localStorage.setItem("cskg_chat_history", JSON.stringify(history));
      window.dispatchEvent(new Event("historyUpdated"));
    } catch (e) {
      console.error("Failed to save history", e);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { id: uuidv4(), role: "user", content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    // Optimistically save to history
    saveToHistory(newMessages);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });

      if (!res.ok) throw new Error("Failed to fetch response");

      const data = await res.json();
      const agentMsg = { id: uuidv4(), role: "agent" as const, content: data.response };

      const updatedMessages = [...newMessages, agentMsg];
      setMessages(updatedMessages);
      saveToHistory(updatedMessages);

    } catch (error) {
      console.error(error);
      const errorMsg = {
        id: uuidv4(),
        role: "agent" as const,
        content: "Sorry, I encountered an error connecting to the API. Make sure the FastAPI server is running."
      };
      setMessages([...newMessages, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className={styles.chatContainer}>
        {messages.map((m) => (
          <div key={m.id} className={`${styles.message} ${m.role === "user" ? styles.messageUser : styles.messageAgent}`}>
            <div className={styles.messageIndicator}>
              {m.role === "user" ? "<" : ">"}
            </div>
            <div className={styles.messageContent}>
              {m.role === "agent" ? (
                <div className={styles.markdownOutput}>
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                </div>
              ) : (
                m.content
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className={styles.message}>
            <div className={styles.loadingDots}>
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputContainer}>
        <form onSubmit={handleSubmit} className={styles.inputForm}>
          <textarea
            className={styles.chatInput}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask about CVEs, vulnerabilities, or attacks..."
            rows={1}
            disabled={isLoading}
          />
          <button type="submit" className={styles.sendBtn} disabled={!input.trim() || isLoading}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'none' }}>
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
      </div>
    </>
  );
}
