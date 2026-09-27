"use client";

/**
 * Renders the 3-option result from POST /negotiate.
 * Props: result = NegotiateResponse (see backend/app/schemas.py), onSelect(optionId)
 */
export default function ItineraryOptions({ result, onSelect }) {
  if (!result) return null;

  return (
    <div className="w-full max-w-5xl">
      <div className="rounded-2xl border border-teal-400/40 bg-white/5 px-6 py-4 mb-4">
        <p className="text-xs font-bold tracking-wider text-teal-400 mb-1">TRAVEX AI</p>
        <p className="text-white italic">&ldquo;{result.ai_message}&rdquo;</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {result.options.map((opt) => {
          const recommended = opt.id === result.recommended_option_id;
          return (
            <div
              key={opt.id}
              className={`rounded-2xl p-5 flex flex-col gap-3 border ${
                recommended ? "border-teal-400" : "border-white/10"
              } bg-white/5`}
            >
              <p className={`text-xs font-bold tracking-wider ${recommended ? "text-teal-400" : "text-slate-400"}`}>
                {recommended ? "RECOMMENDED" : opt.tag}
              </p>
              <p className="text-xl font-bold text-white">{opt.title}</p>

              <div className="text-sm text-slate-300 space-y-1">
                <p>🏨 {opt.hotel}</p>
                <p>🍽 {opt.food}</p>
                <p>🎯 {opt.activities}</p>
              </div>

              <div className="mt-auto pt-3 border-t border-white/10 flex items-center justify-between">
                <p className="text-white font-bold">₹{opt.budget_pp.toLocaleString("en-IN")}</p>
                <button
                  onClick={() => onSelect?.(opt.id)}
                  className="text-xs font-bold tracking-wider text-teal-400 hover:text-teal-300"
                >
                  SELECT
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {result.conflicts.length > 0 && (
        <div className="mt-4 text-xs text-slate-400">
          <span className="font-bold text-[#F76C5E]">Conflicts resolved: </span>
          {result.conflicts.map((c) => c.description).join(" · ")}
        </div>
      )}
    </div>
  );
}
