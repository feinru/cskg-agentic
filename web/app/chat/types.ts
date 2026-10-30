export interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
}

export interface ChatSession {
  preview: string;
  date: string;
  messages: Message[];
}
