import { NextRequest, NextResponse } from "next/server";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { AIMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";

const SPARQL_ENDPOINT = process.env.SPARQL_ENDPOINT || "http://localhost:8890/sparql";

const executeSparqlQuery = tool(
  async ({ query }) => {
    try {
      const response = await fetch(
        `${SPARQL_ENDPOINT}?query=${encodeURIComponent(query)}&format=application%2Fsparql-results%2Bjson`,
        {
          method: "GET",
          headers: {
            Accept: "application/sparql-results+json",
          },
          // Add a small timeout in a real app, native fetch doesn't have an easy timeout config without AbortController
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const bindings = data?.results?.bindings || [];

      // Clean up bindings to a simpler JSON list of dicts for the LLM
      const cleanedResults = bindings.map((row: Record<string, { value: string }>) => {
        const cleanedRow: Record<string, string> = {};
        for (const [k, v] of Object.entries(row)) {
          cleanedRow[k] = v.value;
        }
        return cleanedRow;
      });

      return JSON.stringify(cleanedResults, null, 2);
    } catch (e: unknown) {
      return `Error executing SPARQL query: ${(e as Error).message}`;
    }
  },
  {
    name: "execute_sparql_query",
    description: "Execute a SPARQL query against the Cybersecurity Knowledge Graph (CSKG) and return the results as a JSON string. Use this to fetch data to answer the user's question.",
    schema: z.object({
      query: z.string().describe("The exact SPARQL query to execute"),
    }),
  }
);

const SYSTEM_PROMPT = `You are a Senior SOC Analyst and Knowledge Graph Expert.
Your job is to answer security questions by querying a Cybersecurity Knowledge Graph (CSKG) via SPARQL.

You have access to the \`execute_sparql_query\` tool. 
ALWAYS write and execute a SPARQL query before answering.

Here is the ontology schema you MUST use for your SPARQL queries:
- Prefixes:
  PREFIX cve:   <http://w3id.org/sepses/vocab/ref/cve#>
  PREFIX cwe:   <http://w3id.org/sepses/vocab/ref/cwe#>
  PREFIX capec: <http://w3id.org/sepses/vocab/ref/capec#>
  PREFIX attck: <http://w3id.org/sepses/vocab/ref/attack#>
  PREFIX icsa:  <http://w3id.org/sepses/vocab/ref/icsa#>

- Available Graphs and Relations:
  1. GRAPH <http://w3id.org/sepses/graph/cve>
     - ?cve cve:id ?cveId .
  2. GRAPH <http://w3id.org/sepses/graph/cve_to_cwe>
     - ?cve cve:hasCWE ?cweNode .
  3. GRAPH <http://w3id.org/sepses/graph/cwe>
     - ?cweNode cwe:name ?cweName .
  4. GRAPH <http://w3id.org/sepses/graph/cwe_to_capec>
     - ?cweNode cwe:hasCAPEC ?capecNode .
  5. GRAPH <http://w3id.org/sepses/graph/capec_to_attck>
     - ?capecNode capec:hasRelatedAttackPattern ?attckNode .
  6. GRAPH <http://w3id.org/sepses/graph/attck_enterprise>
     - ?attckNode attck:techniqueId ?techniqueId .
     - ?attckNode attck:name ?techniqueName .
     - ?attckNode attck:description ?techniqueDesc .
  7. GRAPH <http://w3id.org/sepses/graph/icsa> (CISA Known Exploited Vulnerabilities)
     - ?icsaNode a icsa:ICSA .
     - ?icsaNode icsa:cveID ?cveId .
     - ?icsaNode icsa:vendorProject ?vendor .
     - ?icsaNode icsa:product ?product .

When the user asks a question:
1. Write the appropriate SPARQL query string based on the user's intent. 
   - IMPORTANT: If the user mentions a specific product, vendor, or attack technique (e.g., "Apache", "SQL Injection"), you MUST use \`FILTER(regex(?variable, "keyword", "i"))\` to search for it (e.g., \`FILTER(regex(?product, "apache", "i"))\` or \`FILTER(regex(?capecName, "injection", "i"))\`). Do NOT write generic queries without filters unless asked.
2. Show the SPARQL query you will execute.
3. Use the \`execute_sparql_query\` tool to execute it.
4. Read the JSON results.
5. In your FINAL response, ALWAYS start by printing the exact SPARQL query you used inside a markdown code block, then provide a clear, detailed security explanation based on the returned data. Explain *why* the findings matter from a threat intelligence or SOC perspective (just like a real analyst would).`;

export async function POST(req: NextRequest) {
  try {
    const { messages, message } = await req.json();

    let inputMessages = [];
    if (messages && Array.isArray(messages)) {
      // Don't pass the initial static greeting into the LLM context if possible to save tokens, 
      // but if we do, it's fine. We'll map them all.
      inputMessages = messages.map(m =>
        m.role === 'user' ? new HumanMessage(m.content) : new AIMessage(m.content)
      );
    } else if (message) {
      inputMessages = [new HumanMessage(message)];
    } else {
      return NextResponse.json({ error: "Message or messages array is required" }, { status: 400 });
    }

    if (!process.env.GOOGLE_API_KEY) {
      return NextResponse.json({ error: "GOOGLE_API_KEY is not set in the environment" }, { status: 500 });
    }

    const llm = new ChatGoogleGenerativeAI({
      model: "gemini-2.5-flash",
      temperature: 0,
    });

    const agent = createReactAgent({
      llm,
      tools: [executeSparqlQuery],
      stateModifier: new SystemMessage(SYSTEM_PROMPT),
    });

    const events = await agent.stream(
      { messages: inputMessages },
      { streamMode: "values" }
    );

    let finalResponse = "";
    for await (const event of events) {
      const streamEvent = event as unknown as { messages: AIMessage[] };
      const messages = streamEvent.messages;
      const lastMessage = messages[messages.length - 1];

      // We only want the final AI message that is not a tool call request
      if (lastMessage.getType() === "ai" && (!lastMessage.tool_calls || lastMessage.tool_calls.length === 0)) {
        if (typeof lastMessage.content === "string") {
          finalResponse = lastMessage.content;
        } else if (Array.isArray(lastMessage.content)) {
          finalResponse = (lastMessage.content as { text?: string }[])
            .map((block) => block.text || "")
            .join("");
        }
      }
    }

    if (!finalResponse) {
      return NextResponse.json({ error: "No final response from agent" }, { status: 500 });
    }

    return NextResponse.json({ response: finalResponse });
  } catch (error: unknown) {
    console.error("Agent error:", error);
    return NextResponse.json({ error: "Internal Server Error", message: (error as Error).message }, { status: 500 });
  }
}
