import { Message, ChatSession } from "./types";

export function loadSessionMessages(sessionId: string): Message[] | null {
  try {
    const hist = localStorage.getItem("cskg_chat_history");
    if (hist) {
      const parsed: Record<string, ChatSession> = JSON.parse(hist);
      return parsed[sessionId]?.messages || null;
    }
  } catch (e) {
    console.error(e);
  }
  return null;
}

export function saveSessionMessages(sessionId: string, msgs: Message[]): void {
  if (msgs.length <= 1) return;
  try {
    const hist = localStorage.getItem("cskg_chat_history");
    const obj: Record<string, ChatSession> = hist ? JSON.parse(hist) : {};
    const firstUser = msgs.find((m) => m.role === "user");
    obj[sessionId] = {
      preview: firstUser?.content.slice(0, 40) || "Conversation",
      date: new Date().toISOString(),
      messages: msgs,
    };
    localStorage.setItem("cskg_chat_history", JSON.stringify(obj));
    window.dispatchEvent(new Event("historyUpdated"));
  } catch (e) {
    console.error(e);
  }
}
