import type { ReactNode } from "react";

const FEATURES = [
  "AI answers from your own documents",
  "Human handoff when it matters",
  "Embed on any website in one line",
];

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="relative hidden w-[46%] flex-col justify-between overflow-hidden bg-slate-950 p-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-60"
          style={{
            background:
              "radial-gradient(600px 400px at 20% 20%, rgba(99,102,241,0.35), transparent), radial-gradient(500px 400px at 80% 80%, rgba(139,92,246,0.25), transparent)",
          }}
        />
        <div className="relative flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500 text-lg font-bold">
            J
          </div>
          <span className="text-lg font-semibold tracking-tight">Jhinku AI</span>
        </div>

        <div className="relative space-y-6">
          <h1 className="max-w-md text-4xl font-semibold leading-tight tracking-tight">
            Customer support that actually knows your product.
          </h1>
          <ul className="space-y-3">
            {FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-3 text-slate-300">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-xs text-emerald-400">
                  ✓
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-slate-500">
          © Jhinku AI
        </p>
      </div>

      {/* Form side */}
      <div className="flex flex-1 items-center justify-center bg-[#f6f7f9] p-6">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
