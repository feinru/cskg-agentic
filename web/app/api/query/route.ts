import { NextRequest, NextResponse } from "next/server";

const SPARQL_ENDPOINT = process.env.SPARQL_ENDPOINT || "http://localhost:8890/sparql";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const query = (body?.query || "").trim();

    if (!query) {
      return NextResponse.json({ error: "Query cannot be empty" }, { status: 400 });
    }

    let finalQuery = query;
    if (/^\s*(define\s+input:[^\n]+\s+)?select\b/i.test(finalQuery) && !/\blimit\s+\d+/i.test(finalQuery)) {
      finalQuery += "\nLIMIT 100";
    }

    const startTime = Date.now();
    const response = await fetch(
      `${SPARQL_ENDPOINT}?query=${encodeURIComponent(finalQuery)}&format=application%2Fsparql-results%2Bjson`,
      {
        method: "GET",
        headers: {
          Accept: "application/sparql-results+json, application/json, text/plain",
        },
      }
    );

    const elapsedMs = Date.now() - startTime;

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: errorText || `SPARQL endpoint responded with status ${response.status}` },
        { status: 400 }
      );
    }

    const data = await response.json();
    const vars = data?.head?.vars || [];
    const rawBindings = data?.results?.bindings || [];

    const bindings = rawBindings.map((row: Record<string, { type: string; value: string }>) => {
      const entry: Record<string, string> = {};
      for (const [k, v] of Object.entries(row)) {
        entry[k] = v.value;
      }
      return entry;
    });

    return NextResponse.json({
      vars,
      bindings,
      total: bindings.length,
      executionTimeMs: elapsedMs,
      boolean: data.boolean,
    });
  } catch (error: unknown) {
    return NextResponse.json(
      { error: (error as Error).message || "Internal server error" },
      { status: 500 }
    );
  }
}
