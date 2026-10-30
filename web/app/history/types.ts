export interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
}

export interface HistoryItem {
  id: string;
  date: string;
  preview: string;
  messages: Message[];
}
