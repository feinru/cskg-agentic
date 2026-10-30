"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import styles from "./page.module.css";
import { Message } from "./chat/types";
import { MessageItem } from "./chat/message";
import { ChatInput } from "./chat/input";
import { loadSessionMessages, saveSessionMessages } from "./chat/session";

const INITIAL_MESSAGE: Message = {
  id: "init",
  role: "agent",
  content: "Hello, I am your Cybersecurity Knowledge Graph Assistant. Ask me anything about CVEs, attack patterns, defenses, or vulnerabilities.",
};

function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();

  useEffect(() => {
    const session = searchParams.get("session");
    if (session) {
      setSessionId(session);
      const saved = loadSessionMessages(session);
      if (saved) setMessages(saved);
    } else {
      setSessionId(uuidv4());
      setMessages([INITIAL_MESSAGE]);
    }
  }, [searchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const userMsg: Message = { id: uuidv4(), role: "user", content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || err.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const agentMsg: Message = { id: uuidv4(), role: "agent", content: data.response };
      const updated = [...newMessages, agentMsg];
      setMessages(updated);
      saveSessionMessages(sessionId, updated);
    } catch (error: unknown) {
      const errorMsg: Message = { id: uuidv4(), role: "agent", content: `Error: ${(error as Error).message}` };
      setMessages([...newMessages, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className={styles.chatContainer}>
        {messages.map((m) => <MessageItem key={m.id} message={m} />)}
        {isLoading && (
          <div className={styles.message}>
            <div className={styles.loadingDots}><span></span></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput input={input} setInput={setInput} onSubmit={handleSubmit} isLoading={isLoading} />
    </>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ChatApp />
    </Suspense>
  );
}
