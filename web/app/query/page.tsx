"use client";

import { useState, KeyboardEvent } from "react";
import styles from "./page.module.css";
import { PRESETS } from "./presets";
import { QueryTable } from "./table";
import { QueryControls } from "./controls";
import { downloadCsv } from "./export";

export default function QueryPage() {
  const [query, setQuery] = useState(PRESETS[0].query);
  const [selectedPreset, setSelectedPreset] = useState("cve_scores");
  const [isLoading, setIsLoading] = useState(false);
  const [vars, setVars] = useState<string[]>([]);
  const [bindings, setBindings] = useState<Record<string, string>[]>([]);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"table" | "json">("table");

  const handleSelectPreset = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedPreset(e.target.value);
    const found = PRESETS.find((p) => p.id === e.target.value);
    if (found) {
      setQuery(found.query);
      setError(null);
    }
  };

  const handleExecute = async () => {
    if (!query.trim() || isLoading) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      setVars(data.vars || []);
      setBindings(data.bindings || []);
      setExecutionTime(data.executionTimeMs ?? null);
    } catch (err: unknown) {
      setError((err as Error).message);
      setVars([]); setBindings([]); setExecutionTime(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleExecute();
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>SPARQL Workbench</h1>
        <p className={styles.subtitle}>Directly query the Cybersecurity Knowledge Graph (CSKG)</p>
      </div>

      <QueryControls selectedPreset={selectedPreset} onSelectPreset={handleSelectPreset} query={query} setQuery={setQuery} />

      <div className={styles.editorWrapper}>
        <textarea className={styles.editorTextarea} value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={handleKeyDown} spellCheck={false} />
        <div className={styles.editorFooter}>
          <span className={styles.editorHint}>Ctrl + Enter to run | Localhost:8890</span>
          <button type="button" className={styles.runButton} onClick={handleExecute} disabled={isLoading || !query.trim()}>
            {isLoading ? "Executing..." : "Run Query"}
          </button>
        </div>
      </div>

      {error && <div className={styles.errorBanner}>{error}</div>}

      <div className={styles.resultsSection}>
        <div className={styles.resultsHeader}>
          <div className={styles.resultsMetrics}>
            {executionTime !== null && <span>{bindings.length} rows returned ({executionTime}ms)</span>}
          </div>
          <div className={styles.viewTabs}>
            <button type="button" className={`${styles.viewTab} ${activeTab === "table" ? styles.viewTabActive : ""}`} onClick={() => setActiveTab("table")}>Table</button>
            <button type="button" className={`${styles.viewTab} ${activeTab === "json" ? styles.viewTabActive : ""}`} onClick={() => setActiveTab("json")}>JSON</button>
            {bindings.length > 0 && <button type="button" className={styles.viewTab} onClick={() => downloadCsv(vars, bindings)}>Export CSV</button>}
          </div>
        </div>

        {bindings.length > 0 ? (
          activeTab === "table" ? <QueryTable vars={vars} bindings={bindings} /> : <pre className={styles.jsonOutput}><code>{JSON.stringify(bindings, null, 2)}</code></pre>
        ) : !isLoading && !error && (
          <div className={styles.emptyResults}>Run a query to view results.</div>
        )}
      </div>
    </div>
  );
}
