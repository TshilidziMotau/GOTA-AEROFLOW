'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function DashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [cards, setCards] = useState<any[]>([]);

  useEffect(() => {
    api.get(`/projects/${projectId}/tmh16-alignment`).then((r) => setCards(r.data.cards || [])).catch(() => setCards([]));
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <p className="text-sm text-slate-600">TMH16 alignment checklist support (not legal compliance).</p>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      <div className="grid md:grid-cols-2 gap-3">
        {cards.map((c, idx) => (
          <div key={idx} className="border rounded bg-white p-3 text-sm">
            <p className="font-medium">{c.topic}</p>
            <p className="text-xs mt-1">Status: {c.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
export default function DashboardPage() {
  return <div><h1 className="text-xl font-semibold">Dashboard</h1><p>Project pipeline status and TMH16 alignment cards (TODO: wire live metrics).</p></div>;
}
