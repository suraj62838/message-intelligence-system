"use client";

import { useEffect, useState } from "react";
import Navigation from "../components/Navigation";

const API = "/backend";

type SensitiveItem = {
  message_id: string;
  sensitivity_type: string;
  risk: string;
  masked_text: string;
  recommended_action: string;
};

const riskStyles: Record<string, string> = {
  high: "border-red-500/20 bg-red-500/10 text-red-300",
  medium: "border-amber-500/20 bg-amber-500/10 text-amber-300",
  low: "border-blue-500/20 bg-blue-500/10 text-blue-300",
};

export default function SensitivePage() {
  const [items, setItems] = useState<SensitiveItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");

  async function load() {
    try {
      const response = await fetch(`${API}/sensitive`);

      if (!response.ok) {
        throw new Error("Unable to load sensitive information.");
      }

      setItems(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered =
    riskFilter === "all"
      ? items
      : items.filter((item) => item.risk.toLowerCase() === riskFilter);

  return (
    <main className="min-h-screen">
      <Navigation />

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-red-400">
            Part 3
          </p>
          <h1 className="mt-1 text-3xl font-bold">
            Sensitive Information
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500">
            Sensitive values are detected locally and displayed only in masked
            form. Raw secrets are not shown here and should not be sent to an
            external AI service.
          </p>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="mt-8 flex flex-wrap items-center gap-2">
          {["all", "high", "medium", "low"].map((risk) => (
            <button
              key={risk}
              onClick={() => setRiskFilter(risk)}
              className={`rounded-full border px-4 py-2 text-xs font-medium transition ${
                riskFilter === risk
                  ? "border-white/20 bg-white/10 text-white"
                  : "border-white/10 text-zinc-500 hover:bg-white/5 hover:text-zinc-300"
              }`}
            >
              {risk === "all" ? "All" : `${risk[0].toUpperCase()}${risk.slice(1)} risk`}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center text-sm text-zinc-500">
            Loading sensitive messages...
          </div>
        ) : (
          <>
            <div className="mt-6 rounded-2xl border border-red-500/20 bg-red-500/5 p-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-zinc-500">
                    Detected sensitive messages
                  </p>
                  <p className="mt-1 text-3xl font-bold text-red-300">
                    {filtered.length}
                  </p>
                </div>

                <div className="text-right text-xs text-zinc-500">
                  <p>Showing masked values only</p>
                  <p className="mt-1">Recommended action is shown per message</p>
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-4">
              {filtered.map((item) => {
                const risk = item.risk.toLowerCase();

                return (
                  <article
                    key={item.message_id}
                    className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <span className="font-mono text-sm text-cyan-400">
                        {item.message_id}
                      </span>

                      <div className="flex items-center gap-2">
                        <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-zinc-400">
                          {item.sensitivity_type.replaceAll("_", " ")}
                        </span>

                        <span
                          className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                            riskStyles[risk] ??
                            "border-white/10 bg-white/5 text-zinc-300"
                          }`}
                        >
                          {item.risk.toUpperCase()}
                        </span>
                      </div>
                    </div>

                    <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-4">
                      <p className="mb-2 text-xs uppercase tracking-wider text-zinc-600">
                        Masked message
                      </p>
                      <p className="text-sm leading-6 text-zinc-300">
                        {item.masked_text}
                      </p>
                    </div>

                    <div className="mt-4 grid gap-4 md:grid-cols-2">
                      <div>
                        <p className="text-xs uppercase tracking-wider text-zinc-600">
                          Recommended action
                        </p>
                        <p className="mt-1 text-sm text-zinc-200">
                          {item.recommended_action.replaceAll("_", " ")}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-wider text-zinc-600">
                          Privacy rule
                        </p>
                        <p className="mt-1 text-sm text-zinc-400">
                          Process locally and keep the sensitive value masked.
                        </p>
                      </div>
                    </div>
                  </article>
                );
              })}

              {!filtered.length && (
                <div className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-sm text-zinc-500">
                  No sensitive messages match this filter.
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
