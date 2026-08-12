"use client";

import { useEffect, useRef, useState } from "react";
import Navigation from "./components/Navigation";

const API =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

type Stats = {
  total_messages: number;
  categories: Record<string, number>;
  tasks: number;
  events: number;
  sensitive: number;
  processed: number;
};

type Progress = {
  status: "idle" | "processing" | "completed";
  total: number;
  processed: number;
  failed: number;
  percentage: number;
};

type Message = {
  message_id: string;
  timestamp: string;
  sender: string;
  masked_message: string;
  category: string;
  confidence: number;
  reason: string;
};

const categoryStyles: Record<string, string> = {
  "Action Required": "bg-amber-500/15 text-amber-300 border-amber-500/20",
  "Meeting or Event": "bg-blue-500/15 text-blue-300 border-blue-500/20",
  "Personal Information": "bg-purple-500/15 text-purple-300 border-purple-500/20",
  "General Information": "bg-zinc-500/15 text-zinc-300 border-zinc-500/20",
  "Promotional": "bg-pink-500/15 text-pink-300 border-pink-500/20",
  "Sensitive Information": "bg-red-500/15 text-red-300 border-red-500/20",
  Unprocessed: "bg-zinc-500/15 text-zinc-400 border-zinc-500/20",
};

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [progress, setProgress] = useState<Progress>({
    status: "idle",
    total: 0,
    processed: 0,
    failed: 0,
    percentage: 0,
  });

  const [messages, setMessages] = useState<Message[]>([]);
  const [selected, setSelected] = useState<Message | null>(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadName, setUploadName] = useState("");
  const [error, setError] = useState("");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function load() {
    const [statsResponse, messagesResponse, progressResponse] =
      await Promise.all([
        fetch(`${API}/dashboard/stats`),
        fetch(`${API}/messages?limit=50`),
        fetch(`${API}/messages/progress`),
      ]);

    if (!statsResponse.ok) {
      throw new Error(`Stats request failed: ${statsResponse.status}`);
    }

    if (!messagesResponse.ok) {
      throw new Error(`Messages request failed: ${messagesResponse.status}`);
    }

    const [statsData, messagesData, progressData] = await Promise.all([
      statsResponse.json(),
      messagesResponse.json(),
      progressResponse.json(),
    ]);

    setStats(statsData);
    setMessages(messagesData);
    setProgress(progressData);

    if (progressData.status === "processing") {
      setProcessing(true);
    }

    if (progressData.status === "completed") {
      setProcessing(false);
    }
  }

  useEffect(() => {
    load().catch((err) => {
      console.error(err);
      setError(err.message || "Unable to connect to backend.");
    });

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, []);

  function startPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

    pollRef.current = setInterval(async () => {
      try {
        await load();
      } catch (err) {
        console.error(err);
      }
    }, 1000);
  }

  async function upload(file: File) {
    setLoading(true);
    setError("");
    setUploadName(file.name);
    setSelected(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API}/messages/upload`, {
        method: "POST",
        body: formData,
      });

      const text = await response.text();

      if (!response.ok) {
        throw new Error(`Upload failed (${response.status}): ${text}`);
      }

      await load();
    } catch (err) {
      console.error("Upload error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to upload the CSV."
      );
    } finally {
      setLoading(false);
    }
  }

  async function startProcessing() {
    setProcessing(true);
    setError("");

    try {
      const response = await fetch(`${API}/messages/process`, {
        method: "POST",
      });

      const text = await response.text();

      if (!response.ok) {
        throw new Error(`Processing failed (${response.status}): ${text}`);
      }

      startPolling();
      await load();
    } catch (err) {
      console.error("Processing error:", err);
      setProcessing(false);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to start processing."
      );
    }
  }

  const canProcess =
    !!stats &&
    stats.total_messages > 0 &&
    stats.processed < stats.total_messages &&
    !processing &&
    !loading;

  return (
    <main className="min-h-screen">
      <Navigation />

      <header className="border-b border-white/10 bg-zinc-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-end px-6 py-4">
          <div className="flex items-center gap-3">
            {canProcess && (
              <button
                onClick={startProcessing}
                className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-black transition hover:bg-cyan-300"
              >
                Start AI Processing
              </button>
            )}

            <label className="cursor-pointer rounded-xl bg-white px-4 py-2 text-sm font-semibold text-black transition hover:bg-zinc-200">
              {loading ? "Importing..." : "Upload CSV"}

              <input
                type="file"
                accept=".csv"
                className="hidden"
                disabled={loading || processing}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) upload(file);
                }}
              />
            </label>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        {error && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {uploadName && (
          <div className="mb-6 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 text-sm text-zinc-300">
            Dataset:
            <span className="ml-1 font-medium text-white">
              {uploadName}
            </span>

            <span className="ml-2 text-cyan-400">
              imported locally
            </span>
          </div>
        )}

        {processing && (
          <div className="mb-6 rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">AI Processing</p>
                <p className="mt-1 text-sm text-zinc-500">
                  Masked messages are being classified through Groq in batches.
                </p>
              </div>

              <span className="text-lg font-bold text-cyan-400">
                {progress.percentage.toFixed(0)}%
              </span>
            </div>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>

            <div className="mt-3 flex justify-between text-xs text-zinc-500">
              <span>
                {progress.processed} / {progress.total} processed
              </span>
              <span>
                {progress.failed} fallback/failed batches
              </span>
            </div>
          </div>
        )}

        {progress.status === "completed" &&
          progress.total > 0 && (
            <div className="mb-6 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-sm text-emerald-300">
              AI processing completed: {progress.processed} messages processed.
            </div>
          )}

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {[
            ["Messages", stats?.total_messages ?? 0],
            ["Processed", stats?.processed ?? 0],
            ["Actions", stats?.categories?.["Action Required"] ?? 0],
            ["Events", stats?.events ?? 0],
            ["Sensitive", stats?.sensitive ?? 0],
          ].map(([label, value]) => (
            <div
              key={String(label)}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <p className="text-sm text-zinc-500">{label}</p>
              <p className="mt-2 text-3xl font-bold">{value}</p>
            </div>
          ))}
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_380px]">
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02]">
            <div className="border-b border-white/10 px-5 py-4">
              <h2 className="font-semibold">Messages</h2>
              <p className="mt-1 text-sm text-zinc-500">
                Sensitive values are masked before display and before Groq processing.
              </p>
            </div>

            <div className="divide-y divide-white/5">
              {messages.map((message) => (
                <button
                  key={message.message_id}
                  onClick={() => setSelected(message)}
                  className="w-full px-5 py-4 text-left transition hover:bg-white/[0.04]"
                >
                  <div className="flex items-center justify-between gap-4">
                    <span className="font-mono text-xs text-zinc-500">
                      {message.message_id}
                    </span>

                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs ${
                        categoryStyles[message.category] || ""
                      }`}
                    >
                      {message.category}
                    </span>
                  </div>

                  <p className="mt-2 line-clamp-2 text-sm text-zinc-300">
                    {message.masked_message}
                  </p>
                </button>
              ))}

              {!messages.length && (
                <div className="p-10 text-center text-sm text-zinc-500">
                  Upload messages.csv to begin.
                </div>
              )}
            </div>
          </div>

          <aside className="h-fit rounded-2xl border border-white/10 bg-white/[0.02] p-6 lg:sticky lg:top-6">
            {selected ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-zinc-500">
                    {selected.message_id}
                  </span>

                  <span className="text-sm font-semibold text-cyan-400">
                    {(selected.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <h3 className="mt-5 text-lg font-semibold">
                  {selected.category}
                </h3>

                <p className="mt-3 text-sm leading-6 text-zinc-400">
                  {selected.reason}
                </p>

                <div className="mt-6 rounded-xl border border-white/10 bg-black/20 p-4">
                  <p className="mb-2 text-xs uppercase tracking-wider text-zinc-600">
                    Masked message
                  </p>

                  <p className="text-sm leading-6 text-zinc-300">
                    {selected.masked_message}
                  </p>
                </div>

                <div className="mt-5 text-xs text-zinc-600">
                  {selected.timestamp} · {selected.sender}
                </div>
              </>
            ) : (
              <div className="py-10 text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400/10 text-cyan-400">
                  ✓
                </div>

                <h3 className="font-semibold">
                  Select a message
                </h3>

                <p className="mt-2 text-sm text-zinc-500">
                  Classification, confidence, reason, and masked content will appear here.
                </p>
              </div>
            )}
          </aside>
        </section>
      </div>
    </main>
  );
}
