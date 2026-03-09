'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function DetectionReviewPage() {
  const [projectId, setProjectId] = useState('1');
  const [tracks, setTracks] = useState<any[]>([]);

  useEffect(() => {
    api.get(`/projects/${projectId}/tracks`).then((r) => setTracks(r.data)).catch(() => setTracks([]));
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Detection Review</h1>
      <p className="text-sm text-slate-600">Review auto-tracked objects and apply manual corrections before final counts.</p>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      <div className="border rounded bg-white p-3">
        <p className="text-sm font-medium mb-2">Latest tracks: {tracks.length}</p>
        <div className="space-y-1 max-h-72 overflow-auto text-xs">
          {tracks.map((t) => (
            <div key={t.id} className="border p-2 rounded">
              #{t.id} · {t.object_class} · frames {t.start_frame}-{t.end_frame}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
export default function Page() {
  return <div><h1 className="text-xl font-semibold">detection review </h1><p>TODO: implement full module UI with calibration overlays/charts/tables/manual QA.</p></div>;
}
