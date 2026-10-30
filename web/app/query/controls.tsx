"use client";

import styles from "./page.module.css";
import { PRESETS, STANDARD_PREFIXES } from "./presets";

interface ControlsProps {
  selectedPreset: string;
  onSelectPreset: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  query: string;
  setQuery: (q: string) => void;
}

export function QueryControls({ selectedPreset, onSelectPreset, query, setQuery }: ControlsProps) {
  return (
    <div className={styles.controls}>
      <select className={styles.presetsSelect} value={selectedPreset} onChange={onSelectPreset}>
        {PRESETS.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
      <div className={styles.buttonGroup}>
        <button
          type="button"
          className={styles.actionButton}
          onClick={() => !query.includes("DEFINE input:inference") && setQuery(`DEFINE input:inference "cskg"\n${query}`)}
        >
          [+ Inference "cskg"]
        </button>
        <button
          type="button"
          className={styles.actionButton}
          onClick={() => !query.includes("PREFIX cve:") && setQuery(`${STANDARD_PREFIXES}\n\n${query}`)}
        >
          [+ Prefixes]
        </button>
        <button type="button" className={styles.actionButton} onClick={() => setQuery("")}>
          [Clear]
        </button>
      </div>
    </div>
  );
}
