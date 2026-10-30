"use client";

import { KeyboardEvent } from "react";
import styles from "../page.module.css";

interface ChatInputProps {
  input: string;
  setInput: (val: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
}

export function ChatInput({ input, setInput, onSubmit, isLoading }: ChatInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  return (
    <div className={styles.inputContainer}>
      <form onSubmit={onSubmit} className={styles.inputForm}>
        <textarea
          className={styles.chatInput}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about CVEs, vulnerabilities, or attacks..."
          rows={1}
          disabled={isLoading}
        />
        <button
          type="submit"
          className={styles.sendBtn}
          disabled={!input.trim() || isLoading}
        />
      </form>
    </div>
  );
}
