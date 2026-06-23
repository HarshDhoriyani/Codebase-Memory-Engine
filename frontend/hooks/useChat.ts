"use client";
import { useState, useCallback } from "react";
import { explainStream } from "@/lib/api";

export interface Message {
  id:       string;
  role:     "user" | "assistant";
  content:  string;
  intent?:  string;
  function?: string;
  loading?: boolean;
}

export function useChat() {
  const [messages,   setMessages]   = useState<Message[]>([]);
  const [isLoading,  setIsLoading]  = useState(false);
  const [lastIntent, setLastIntent] = useState<string>("");

  const sendMessage = useCallback((query: string) => {
    if (!query.trim() || isLoading) return;

    const userMsg: Message = {
      id:      crypto.randomUUID(),
      role:    "user",
      content: query,
    };

    const assistantMsg: Message = {
      id:      crypto.randomUUID(),
      role:    "assistant",
      content: "",
      loading: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);

    let accumulated = "";

    explainStream(
      query,
      (meta) => {
        setLastIntent(meta.intent);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, intent: meta.intent, function: meta.function }
              : m
          )
        );
      },
      (chunk) => {
        accumulated += chunk;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: accumulated }
              : m
          )
        );
      },
      () => {
        setIsLoading(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, loading: false }
              : m
          )
        );
      },
      (err) => {
        setIsLoading(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: `Error: ${err}`, loading: false }
              : m
          )
        );
      }
    );
  }, [isLoading]);

  return { messages, isLoading, lastIntent, sendMessage };
}