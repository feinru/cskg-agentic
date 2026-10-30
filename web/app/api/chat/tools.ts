import { tool } from "@langchain/core/tools";
import { z } from "zod";

const SPARQL_ENDPOINT = process.env.SPARQL_ENDPOINT || "http://localhost:8890/sparql";

export const executeSparqlQuery = tool(
  async ({ query }) => {
    try {
      let safeQuery = query.trim();
      if (!/limit\s+\d+/i.test(safeQuery)) {
        safeQuery += " LIMIT 50";
      }

      const response = await fetch(
        `${SPARQL_ENDPOINT}?query=${encodeURIComponent(safeQuery)}&format=application%2Fsparql-results%2Bjson`,
        {
          method: "GET",
          headers: {
            Accept: "application/sparql-results+json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const bindings = data?.results?.bindings || [];
      const maxRows = 50;
      const sliced = bindings.slice(0, maxRows);
      const cleaned = sliced.map((row: Record<string, { value: string }>) => {
        const item: Record<string, string> = {};
        for (const [k, v] of Object.entries(row)) {
          item[k] = v.value;
        }
        return item;
      });

      let jsonOutput = JSON.stringify(cleaned, null, 2);
      if (bindings.length > maxRows) {
        jsonOutput += `\n\n[Notice: Truncated to first ${maxRows} records out of ${bindings.length} total rows]`;
      }
      return jsonOutput;
    } catch (e: unknown) {
      return `Error executing SPARQL query: ${(e as Error).message}`;
    }
  },
  {
    name: "execute_sparql_query",
    description: "Execute a SPARQL query against the CSKG knowledge graph and return results as JSON.",
    schema: z.object({
      query: z.string().describe("The exact SPARQL query to execute"),
    }),
  }
);
