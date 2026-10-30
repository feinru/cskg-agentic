export function downloadCsv(vars: string[], bindings: Record<string, string>[]) {
  if (!vars.length || !bindings.length) return;
  const header = vars.join(",");
  const rows = bindings.map((row) =>
    vars.map((v) => `"${(row[v] || "").replace(/"/g, '""')}"`).join(",")
  );
  const blob = new Blob([header + "\n" + rows.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `sparql_export_${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
