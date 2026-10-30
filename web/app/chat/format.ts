export function normalizeMarkdown(text: string): string {
  if (!text) return "";

  let cleaned = text;

  cleaned = cleaned.replace(/([^\n])```/g, "$1\n\n```");
  cleaned = cleaned.replace(/```([a-zA-Z0-9_-]+)([^\n])/g, "```$1\n$2");
  cleaned = cleaned.replace(/```\s*\n\s*```/g, "");

  cleaned = cleaned.replace(
    /```(?:text|markdown)?\s*\n([\s\S]*?\*\*[0-9]+[\s\S]*?)```/g,
    "$1"
  );

  cleaned = cleaned.replace(/\n {4,}(\*\*|\*|###|- )/g, "\n$1");

  return cleaned.trim();
}

export function formatUriLabel(href: string): string {
  if (!href) return "";
  if (href.includes("w3id.org/sepses/vocab/ref/")) {
    const parts = href.split("ref/");
    return parts[1] || href;
  }
  if (href.includes("w3id.org/sepses/graph/")) {
    const parts = href.split("graph/");
    return `graph:${parts[1] || href}`;
  }
  if (href.includes("w3id.org/sepses/resource/")) {
    const parts = href.split("resource/");
    return parts[1] || href;
  }
  return href;
}
