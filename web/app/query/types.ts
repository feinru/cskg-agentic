export interface PresetQuery {
  id: string;
  name: string;
  query: string;
}

export interface QueryResponse {
  vars: string[];
  bindings: Record<string, string>[];
  total: number;
  executionTimeMs: number;
  error?: string;
}
