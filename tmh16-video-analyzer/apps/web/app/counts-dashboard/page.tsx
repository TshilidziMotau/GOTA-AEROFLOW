'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function CountsDashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [data, setData] = useState<any>(null);
  const [message, setMessage] = useState('');

  const load = () => {
    api.get(`/projects/${projectId}/counts`).then((r) => setData(r.data)).catch(() => setData(null));
  };

  useEffect(() => {
    load();
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Counts Dashboard</h1>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      {!data ? (
        <p>No data available.</p>
      ) : (
        <div className="border rounded bg-white p-3 text-sm space-y-2">
          <p className="font-medium">Peak interval</p>
          <pre className="text-xs overflow-auto">{JSON.stringify(data.peak_interval, null, 2)}</pre>
          <p className="text-xs text-slate-600">{data.assumption_note}</p>
          <button className="border px-3 py-2" onClick={async () => {
            try {
              await api.post(`/projects/${projectId}/manual-corrections`, { edit_type: 'approve_counts', payload: { approved: true, peak_interval: data.peak_interval } });
              setMessage('Counts approval recorded in audit trail.');
            } catch {
              setMessage('Failed to record approval.');
            }
          }}>Approve Counts for Report</button>
          {message && <p className="text-xs">{message}</p>}
        </div>
      )}
    </div>
  );
}
