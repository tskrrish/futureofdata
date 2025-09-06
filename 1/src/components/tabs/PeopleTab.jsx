import { Trophy } from "lucide-react";
import { CommentsSection } from "../comments/CommentsSection";

export function PeopleTab({ leaderboard, badges }) {
  return (
    <div className="grid lg:grid-cols-2 gap-6 mt-4">
      <div className="rounded-2xl border bg-white p-4">
        <h3 className="font-semibold mb-3">Top Volunteers (Hours)</h3>
        <ul className="space-y-3">
          {leaderboard.map((row, i) => (
            <li key={row.assignee} className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded-xl border bg-white">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-neutral-100 grid place-items-center font-semibold">{i + 1}</div>
                  <div>
                    <div className="font-medium">{row.assignee}</div>
                    <div className="text-xs text-neutral-500">{row.hours} hours</div>
                  </div>
                </div>
                <Trophy className="w-4 h-4" />
              </div>
              <CommentsSection 
                entityType="volunteer" 
                entityId={row.assignee}
                entityName={row.assignee}
              />
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl border bg-white p-4">
        <h3 className="font-semibold mb-3">Badges Earned</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          {badges.map((b) => (
            <div key={b.assignee} className="p-3 rounded-xl border bg-white">
              <div className="font-medium mb-1">{b.assignee}</div>
              <div className="text-xs text-neutral-500 mb-2">{b.hours} total hours</div>
              <div className="flex flex-wrap gap-2">
                {b.badges.map((m) => (
                  <span key={m} className="px-2 py-1 rounded-full text-xs border">{m}+ hrs</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}