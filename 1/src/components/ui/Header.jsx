import { Download } from "lucide-react";
import AnnouncementNotification from "../announcements/AnnouncementNotification";

export function Header({ onFileUpload, onExportRaw }) {
  return (
    <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-black/90 text-white grid place-items-center font-bold">Y</div>
          <div>
            <h1 className="text-xl font-semibold">YMCA Volunteer Dashboard</h1>
            <p className="text-xs text-neutral-500">Belonging by Design — powered by VolunteerMatters data</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <AnnouncementNotification />
          <input
            id="file"
            type="file"
            accept=".csv,.json"
            onChange={onFileUpload}
            className="block w-56 text-sm text-neutral-700 file:mr-2 file:py-1.5 file:px-3 file:rounded-xl file:border file:bg-white file:hover:bg-neutral-50 file:cursor-pointer"
          />
          <button
            onClick={onExportRaw}
            className="inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-sm hover:bg-neutral-50"
          >
            <Download className="w-4 h-4" /> Export Raw
          </button>
        </div>
      </div>
    </header>
  );
}