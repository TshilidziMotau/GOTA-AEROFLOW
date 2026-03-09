'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function SchoolModeDashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.get(`/projects/${projectId}/school-mode`).then((r) => setData(r.data)).catch(() => setData(null));
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">School Mode Dashboard</h1>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      {!data ? <p>No school mode data available.</p> : (
        <div className="border rounded bg-white p-3 text-sm space-y-2">
          <p>Queue peak: <strong>{data.queue_peak || 0}</strong></p>
          <p>Pedestrian activity: <strong>{data.pedestrian_activity || 0}</strong></p>
          <p className="font-medium">Flags</p>
          <ul className="list-disc pl-6 text-xs">{(data.flags || []).map((f: string) => <li key={f}>{f}</li>)}</ul>
          <p className="text-xs text-slate-600">{data.review_note}</p>
        </div>
      )}
    </div>
  );
export default function Page() {
  return <div><h1 className="text-xl font-semibold">school mode dashboard </h1><p>TODO: implement full module UI with calibration overlays/charts/tables/manual QA.</p></div>;
}
