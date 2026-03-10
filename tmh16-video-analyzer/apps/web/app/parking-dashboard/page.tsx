'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function ParkingDashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.get(`/projects/${projectId}/parking`).then((r) => setData(r.data)).catch(() => setData(null));
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Parking Dashboard</h1>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      {!data ? <p>No parking data available.</p> : (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p>Detected stops: <strong>{(data.occupancy || []).length}</strong></p>
          <p>Short stay count: <strong>{data.short_stay_count || 0}</strong></p>
          <p>Turnover estimate: <strong>{data.turnover_estimate || 0}</strong></p>
        </div>
      )}
    </div>
  );
}
