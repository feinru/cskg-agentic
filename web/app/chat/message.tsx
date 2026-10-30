"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import styles from "../page.module.css";
import { Message } from "./types";
import { normalizeMarkdown, formatUriLabel } from "./format";

interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 1500);
  };

  if (message.role === "user") {
    return (
      <div className={`${styles.message} ${styles.messageUser}`}>
        <div className={styles.messageIndicator}>&lt;</div>
        <div className={styles.messageContent}>{message.content}</div>
      </div>
    );
  }

  const content = normalizeMarkdown(message.content);

  return (
    <div className={`${styles.message} ${styles.messageAgent}`}>
      <div className={styles.messageIndicator}>&gt;</div>
      <div className={styles.messageContent}>
        <div className={styles.markdownOutput}>
          <ReactMarkdown
            components={{
              pre({ children }) {
                return <div className={styles.codeBlockWrapper}>{children}</div>;
              },
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || "");
                const codeString = String(children).replace(/\n$/, "");
                const isBlock = Boolean(match) || codeString.includes("\n");

                if (isBlock) {
                  return (
                    <div className={styles.codeContainer}>
                      <div className={styles.codeHeader}>
                        <span>{match ? match[1].toUpperCase() : "SPARQL"}</span>
                        <button
                          type="button"
                          className={styles.copyCodeButton}
                          onClick={() => handleCopy(codeString)}
                        >
                          {copiedCode === codeString ? "Copied" : "Copy"}
                        </button>
                      </div>
                      <pre className={styles.codePre}>
                        <code {...props}>{codeString}</code>
                      </pre>
                    </div>
                  );
                }
                return <code className={styles.inlineCode} {...props}>{children}</code>;
              },
              a({ href, children }) {
                const url = href || "";
                if (url.includes("w3id.org/sepses") || url.includes("d3fend.mitre.org")) {
                  return <code className={styles.uriBadge} title={url}>{formatUriLabel(url)}</code>;
                }
                return <a href={url} target="_blank" rel="noopener noreferrer">{children}</a>;
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
