'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function CountsDashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.get(`/projects/${projectId}/counts`).then((r) => setData(r.data)).catch(() => setData(null));
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Counts Dashboard</h1>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      {!data ? (
        <p>No data available.</p>
      ) : (
        <div className="border rounded bg-white p-3 text-sm">
          <p className="font-medium">Peak interval</p>
          <pre className="text-xs overflow-auto">{JSON.stringify(data.peak_interval, null, 2)}</pre>
          <p className="text-xs text-slate-600">{data.assumption_note}</p>
        </div>
      )}
    </div>
  );
export default function Page() {
  return <div><h1 className="text-xl font-semibold">counts dashboard </h1><p>TODO: implement full module UI with calibration overlays/charts/tables/manual QA.</p></div>;
}
