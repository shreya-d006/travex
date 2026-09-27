"use client";
import { useState } from "react";
import { useGroupChat } from "../hooks/useGroupChat";

const SENDER_COLORS = [
  "#2DD4BF", // teal
  "#3B82F6", // blue
  "#8B5CF6", // purple
  "#F76C5E", // coral
];

function colorFor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return SENDER_COLORS[Math.abs(hash) % SENDER_COLORS.length];
}

/**
 * Props:
 *   tripId       - Firestore doc id for this trip's chat
 *   currentUser  - the name this device/browser is sending as
 *   onNegotiate  - async (messages) => NegotiateResponse; called when the
 *                  "Ask Travex" button is pressed. Wire this to your
 *                  backend's POST /negotiate.
 */
export default function ChatWindow({ tripId, currentUser, onNegotiate }) {
  const { messages, sendMessage } = useGroupChat(tripId);
  const [draft, setDraft] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  const handleSend = () => {
    if (!draft.trim()) return;
    sendMessage(currentUser, draft);
    setDraft("");
  };

  const handleAskTravex = async () => {
    setAnalyzing(true);
    try {
      await onNegotiate(messages);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-md rounded-2xl border border-white/10 bg-[#0B1120] overflow-hidden">
      <div className="px-4 py-3 border-b border-white/10">
        <p className="text-xs tracking-wider text-slate-400 font-semibold">GROUP CHAT</p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((m) => {
          const mine = m.sender === currentUser;
          const color = colorFor(m.sender);
          return (
            <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
              <div
                className="max-w-[80%] rounded-xl px-3 py-2"
                style={{ backgroundColor: `${color}22`, border: `1px solid ${color}66` }}
              >
                <p className="text-xs font-bold mb-0.5" style={{ color }}>
                  {m.sender}
                </p>
                <p className="text-sm text-white italic">&ldquo;{m.text}&rdquo;</p>
              </div>
            </div>
          );
        })}

        {analyzing && (
          <div className="flex justify-center pt-2">
            <div className="rounded-full border border-teal-400 px-4 py-2 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
              <span className="text-sm italic text-white">Travex is analyzing the conversation…</span>
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-white/10 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a message…"
          className="flex-1 rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm text-white placeholder:text-slate-500 outline-none focus:border-teal-400"
        />
        <button
          onClick={handleSend}
          className="rounded-lg px-3 py-2 text-sm font-semibold bg-white/10 text-white hover:bg-white/20"
        >
          Send
        </button>
      </div>

      <div className="p-3 pt-0">
        <button
          onClick={handleAskTravex}
          disabled={analyzing || messages.length === 0}
          className="w-full rounded-full py-2 text-sm font-bold text-[#0B1120] bg-teal-400 hover:bg-teal-300 disabled:opacity-40"
        >
          Ask Travex to negotiate →
        </button>
      </div>
    </div>
  );
}
