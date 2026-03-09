'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function QueueDashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.get(`/projects/${projectId}/queues`).then((r) => setData(r.data)).catch(() => setData(null));
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Queue Dashboard</h1>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      {!data ? <p>No queue data available.</p> : (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p>Average queue: <strong>{Number(data.average_queue || 0).toFixed(2)}</strong></p>
          <p>Max queue: <strong>{data.max_queue || 0}</strong></p>
          <p>Queue duration (s): <strong>{Number(data.queue_duration_s || 0).toFixed(1)}</strong></p>
          <p className="text-xs text-slate-600">{data.queue_summary}</p>
        </div>
      )}
    </div>
  );
export default function Page() {
  return <div><h1 className="text-xl font-semibold">queue dashboard </h1><p>TODO: implement full module UI with calibration overlays/charts/tables/manual QA.</p></div>;
}
