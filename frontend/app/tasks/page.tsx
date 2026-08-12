"use client";

import { useEffect, useState } from "react";
import Navigation from "../components/Navigation";

const API =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

type Item = {
  item_id: string;
  type: "task" | "event";
  title: string;
  description: string | null;
  date_or_deadline: string | null;
  time: string | null;
  person: string | null;
  priority: string | null;
  source_message_id: string;
};

function ItemCard({ item }: { item: Item }) {
  const isTask = item.type === "task";

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <span
            className={`inline-flex rounded-full border px-2.5 py-1 text-xs ${
              isTask
                ? "border-amber-500/20 bg-amber-500/10 text-amber-300"
                : "border-blue-500/20 bg-blue-500/10 text-blue-300"
            }`}
          >
            {isTask ? "Task" : "Event"}
          </span>

          <h2 className="mt-3 text-lg font-semibold">{item.title}</h2>
        </div>

        {item.priority && (
          <span className="rounded-full border border-white/10 px-2.5 py-1 text-xs text-zinc-400">
            {item.priority}
          </span>
        )}
      </div>

      {item.description && (
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          {item.description}
        </p>
      )}

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-600">
            Date / Deadline
          </p>
          <p className="mt-1 text-sm text-zinc-200">
            {item.date_or_deadline ?? "Unresolved"}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-600">
            Time
          </p>
          <p className="mt-1 text-sm text-zinc-200">
            {item.time ?? "Unresolved"}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-600">
            Person
          </p>
          <p className="mt-1 text-sm text-zinc-200">
            {item.person ?? "Unresolved"}
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-600">
            Source Message
          </p>
          <p className="mt-1 font-mono text-sm text-cyan-400">
            {item.source_message_id}
          </p>
        </div>
      </div>
    </article>
  );
}

export default function TasksEventsPage() {
  const [tasks, setTasks] = useState<Item[]>([]);
  const [events, setEvents] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [tasksResponse, eventsResponse] = await Promise.all([
        fetch(`${API}/tasks`),
        fetch(`${API}/events`),
      ]);

      if (!tasksResponse.ok || !eventsResponse.ok) {
        throw new Error("Unable to load tasks and events.");
      }

      const [tasksData, eventsData] = await Promise.all([
        tasksResponse.json(),
        eventsResponse.json(),
      ]);

      setTasks(tasksData);
      setEvents(eventsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="min-h-screen">
      <Navigation />

      <div className="mx-auto max-w-7xl px-6 py-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">
            Part 2
          </p>
          <h1 className="mt-1 text-3xl font-bold">Tasks & Events</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            Extracted tasks, reminders, meetings, and events. Missing dates,
            times, or people are shown as unresolved instead of being guessed.
          </p>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {loading ? (
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center text-sm text-zinc-500">
            Loading extracted items...
          </div>
        ) : (
          <div className="mt-8 grid gap-8 lg:grid-cols-2">
            <section>
              <div className="mb-4 flex items-end justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Tasks</h2>
                  <p className="mt-1 text-sm text-zinc-500">
                    {tasks.length} extracted task{tasks.length === 1 ? "" : "s"}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {tasks.map((item) => (
                  <ItemCard key={item.item_id} item={item} />
                ))}

                {!tasks.length && (
                  <div className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-sm text-zinc-500">
                    No tasks extracted yet. Process the dataset first.
                  </div>
                )}
              </div>
            </section>

            <section>
              <div className="mb-4">
                <h2 className="text-xl font-semibold">Events</h2>
                <p className="mt-1 text-sm text-zinc-500">
                  {events.length} extracted event{events.length === 1 ? "" : "s"}
                </p>
              </div>

              <div className="space-y-4">
                {events.map((item) => (
                  <ItemCard key={item.item_id} item={item} />
                ))}

                {!events.length && (
                  <div className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-sm text-zinc-500">
                    No events extracted yet. Process the dataset first.
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
