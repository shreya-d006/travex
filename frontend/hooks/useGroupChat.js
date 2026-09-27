"use client";
import { useEffect, useState, useCallback } from "react";
import {
  collection,
  addDoc,
  query,
  orderBy,
  onSnapshot,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "../lib/firebase";

/**
 * Real-time group chat for a single trip.
 * Every participant's browser/device calls this with the same tripId and
 * they all see each other's messages live via Firestore's onSnapshot.
 *
 * Usage:
 *   const { messages, sendMessage } = useGroupChat("trip_goa_2026");
 *   sendMessage("Shreya", "Food is non-negotiable. Michelin stars only!");
 */
export function useGroupChat(tripId) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tripId) return;
    const q = query(
      collection(db, "trips", tripId, "messages"),
      orderBy("createdAt", "asc")
    );
    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        setMessages(snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() })));
        setLoading(false);
      },
      (err) => {
        console.error("Chat listener error:", err);
        setLoading(false);
      }
    );
    return () => unsubscribe();
  }, [tripId]);

  const sendMessage = useCallback(
    async (sender, text) => {
      if (!tripId || !text.trim()) return;
      await addDoc(collection(db, "trips", tripId, "messages"), {
        sender,
        text: text.trim(),
        createdAt: serverTimestamp(),
      });
    },
    [tripId]
  );

  return { messages, loading, sendMessage };
}
