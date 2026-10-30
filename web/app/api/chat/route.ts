import { NextRequest, NextResponse } from "next/server";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { AIMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";
import { SYSTEM_PROMPT } from "./prompt";
import { executeSparqlQuery } from "./tools";

export async function POST(req: NextRequest) {
  try {
    const { messages, message } = await req.json();

    let inputMessages = [];
    if (messages && Array.isArray(messages)) {
      inputMessages = messages.map((m) =>
        m.role === "user" ? new HumanMessage(m.content) : new AIMessage(m.content)
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

    const events = await agent.stream({ messages: inputMessages }, { streamMode: "values" });

    let finalResponse = "";
    for await (const event of events) {
      const streamEvent = event as unknown as { messages: AIMessage[] };
      const currentMessages = streamEvent.messages;
      const lastMessage = currentMessages[currentMessages.length - 1];

      if (lastMessage.getType() === "ai" && (!lastMessage.tool_calls || lastMessage.tool_calls.length === 0)) {
        if (typeof lastMessage.content === "string") {
          finalResponse = lastMessage.content;
        } else if (Array.isArray(lastMessage.content)) {
          finalResponse = (lastMessage.content as { text?: string }[])
            .map((b) => b.text || "")
            .join("");
        }
      }
    }

    if (!finalResponse) {
      return NextResponse.json({ error: "No final response from agent" }, { status: 500 });
    }

    return NextResponse.json({ response: finalResponse });
  } catch (error: unknown) {
    return NextResponse.json(
      { error: "Internal Server Error", message: (error as Error).message },
      { status: 500 }
    );
  }
}
