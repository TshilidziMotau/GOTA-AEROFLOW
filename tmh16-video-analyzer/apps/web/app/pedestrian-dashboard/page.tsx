'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function PedestrianDashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.get(`/projects/${projectId}/pedestrians`).then((r) => setData(r.data)).catch(() => setData(null));
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Pedestrian Dashboard</h1>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      {!data ? <p>No pedestrian data available.</p> : (
        <div className="border rounded bg-white p-3 text-sm">
          <p>Total crossings: <strong>{data.total_crossings || 0}</strong></p>
          <pre className="text-xs overflow-auto mt-2">{JSON.stringify(data.crossing_counts, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
