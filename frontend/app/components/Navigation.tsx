import Link from "next/link";

export default function Navigation() {
  return (
    <nav className="border-b border-white/10 bg-zinc-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-semibold tracking-tight">
          Message Intelligence
        </Link>

        <div className="flex items-center gap-2 text-sm">
          <Link
            href="/"
            className="rounded-lg px-3 py-2 text-zinc-400 transition hover:bg-white/5 hover:text-white"
          >
            Dashboard
          </Link>
          <Link
            href="/tasks"
            className="rounded-lg px-3 py-2 text-zinc-400 transition hover:bg-white/5 hover:text-white"
          >
            Tasks & Events
          </Link>
          <Link
            href="/sensitive"
            className="rounded-lg px-3 py-2 text-zinc-400 transition hover:bg-white/5 hover:text-white"
          >
            Sensitive
          </Link>
        </div>
      </div>
    </nav>
  );
}
