"use client";
import { useState } from "react";
import ChatWindow from "./ChatWindow";
import ItineraryOptions from "./ItineraryOptions";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Example page wiring everything together end-to-end.
// Copy into app/trip/[tripId]/page.jsx and adjust as needed.
export default function TripPage() {
  const [result, setResult] = useState(null);

  const handleNegotiate = async (messages) => {
    const res = await fetch(`${API_URL}/negotiate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        trip_name: "Trip to Goa",
        participants: ["Shreya", "Rayan", "Mohammed Zayan", "Mohammed Huzaif"],
        messages: messages.map((m) => ({ sender: m.sender, text: m.text })),
        budget_pp: 2500,
      }),
    });
    if (!res.ok) throw new Error("Negotiation failed");
    const data = await res.json();
    setResult(data);
  };

  return (
    <main className="min-h-screen bg-[#0B1120] flex flex-col items-center gap-8 p-8">
      <h1 className="text-3xl font-black text-[#F5E9DC]">TRAVEX — Trip to Goa</h1>

      <ChatWindow tripId="trip_goa_2026" currentUser="Shreya" onNegotiate={handleNegotiate} />

      <ItineraryOptions result={result} onSelect={(id) => console.log("selected", id)} />
    </main>
  );
}
