"use client";

import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Send, AlertCircle } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import ReactMarkdown from "react-markdown";
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { api } from "@/lib/api";

const SUGGESTED_QUESTIONS = [
  "Which invoices have incorrect GST calculations?",
  "Show me all high severity anomalies",
  "Are there any suspicious cancellations?",
  "Explain the service charge violations",
  "Which online orders have tax double-count risk?",
  "What are the most common policy violations?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! I'm Cognify's AI auditor. Ask me anything about the anomalies detected in your uploaded dataset.\n\nFor example: *\"Which invoices have tax calculation errors?\"* or *\"Explain the high severity anomalies.\"*",
    },
  ]);
  const [input, setInput]         = useState("");
  const [isTyping, setIsTyping]   = useState(false);
  const [sessionActive, setSessionActive] = useState(null);
  const bottomRef = useRef(null);

  // Check if audit session is active
  useEffect(() => {
    api.status()
      .then((s) => setSessionActive(s.session_active))
      .catch(() => setSessionActive(false));
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = async (question) => {
    const text = question || input.trim();
    if (!text) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsTyping(true);

    try {
      const data = await api.ask(text);

      let responseText = data.answer || "No response received.";

      // Append retrieved invoice references if available
      if (data.top_invoices?.length) {
        const invoices = data.top_invoices.filter(Boolean);
        if (invoices.length) {
          responseText += `\n\n*Referenced invoices: ${invoices.join(", ")}*`;
        }
      }

      setMessages((prev) => [...prev, { role: "assistant", text: responseText }]);
    } catch (err) {
      const errMsg = err.message.includes("No audit data")
        ? "No audit session found. Please upload a CSV on the **Audit** page first, then come back to ask questions."
        : `Sorry, something went wrong: ${err.message}`;
      setMessages((prev) => [...prev, { role: "assistant", text: errMsg }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem><BreadcrumbPage>Chat</BreadcrumbPage></BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
            {sessionActive === false && (
              <div className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-3 py-1 ml-2">
                <AlertCircle className="w-3 h-3" />
                No audit session — upload a CSV on the Audit page first
              </div>
            )}
            {sessionActive === true && (
              <div className="flex items-center gap-1 text-xs text-green-600 bg-green-50 border border-green-200 rounded-full px-3 py-1 ml-2">
                ● Audit session active
              </div>
            )}
          </div>
        </header>

        <main className="flex flex-col h-[calc(100vh-4rem)]">
          <ScrollArea className="flex-1 px-4 md:px-6 py-6">
            <div className="flex flex-col gap-6 max-w-3xl mx-auto">

              {messages.map((msg, idx) => (
                <div key={idx} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`rounded-2xl px-6 py-4 max-w-2xl shadow-sm ${
                    msg.role === "user"
                      ? "bg-black text-white"
                      : "bg-white text-gray-800 border border-gray-200"
                  }`}>
                    <div className="text-base leading-relaxed prose prose-sm max-w-none">
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="rounded-2xl px-6 py-4 bg-white text-gray-800 border border-gray-200 shadow-sm">
                    <div className="flex gap-1">
                      {[0, 200, 400].map((delay) => (
                        <div key={delay} className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          </ScrollArea>

          {/* Suggested questions */}
          {messages.length <= 1 && (
            <div className="px-4 md:px-6 pb-2">
              <div className="max-w-3xl mx-auto flex flex-wrap gap-2">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="px-3 py-1 text-xs bg-muted rounded-full border border-gray-200 hover:border-gray-400 hover:bg-white transition text-gray-600"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          <footer className="border-t border-gray-200 bg-white p-4 md:p-6">
            <div className="max-w-3xl mx-auto">
              <div className="flex gap-2 items-center bg-white rounded-lg border border-gray-300 focus-within:ring-1 focus-within:border-transparent p-1">
                <Input
                  className="flex-1 border-none shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 text-base"
                  placeholder="Ask about anomalies in your dataset..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                  disabled={isTyping}
                />
                <Button
                  onClick={() => handleSend()}
                  size="icon"
                  disabled={isTyping || !input.trim()}
                  className="bg-black hover:bg-gray-800 text-white h-10 w-10 rounded-lg"
                >
                  <Send className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </footer>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
