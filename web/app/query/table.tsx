"use client";

import { useState } from "react";
import styles from "./page.module.css";

interface TableProps {
  vars: string[];
  bindings: Record<string, string>[];
}

export function QueryTable({ vars, bindings }: TableProps) {
  const [copiedCell, setCopiedCell] = useState<string | null>(null);

  const handleCopy = (value: string) => {
    navigator.clipboard.writeText(value);
    setCopiedCell(value);
    setTimeout(() => setCopiedCell(null), 1500);
  };

  const formatCellValue = (value: string) => {
    if (!value) return "-";
    if (value.startsWith("http://") || value.startsWith("https://") || value.startsWith("urn:")) {
      const parts = value.split(/[#/]/);
      return parts[parts.length - 1] || value;
    }
    return value;
  };

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.resultsTable}>
        <thead>
          <tr>
            <th className={styles.rowNumber}>#</th>
            {vars.map((v) => (
              <th key={v}>?{v}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bindings.map((row, idx) => (
            <tr key={idx}>
              <td className={styles.rowNumber}>{idx + 1}</td>
              {vars.map((v) => {
                const raw = row[v] || "";
                const isUri =
                  raw.startsWith("http://") || raw.startsWith("https://") || raw.startsWith("urn:");
                return (
                  <td
                    key={v}
                    title={raw}
                    className={isUri ? styles.uriCell : ""}
                    onClick={() => handleCopy(raw)}
                  >
                    {formatCellValue(raw)}
                    {copiedCell === raw && " (copied)"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
