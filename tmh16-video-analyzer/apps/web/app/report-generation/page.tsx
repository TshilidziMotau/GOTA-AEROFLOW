'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function ReportGenerationPage() {
  const [projectId, setProjectId] = useState('1');
  const [exportsList, setExportsList] = useState<any[]>([]);
  const [message, setMessage] = useState('');

  const refreshExports = () => {
    api.get(`/projects/${projectId}/exports`).then((r) => setExportsList(r.data)).catch(() => setExportsList([]));
  };

  useEffect(() => {
    refreshExports();
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Report Generation</h1>
      <p className="text-sm text-slate-600">Generate draft TMH16 evidence exports (HTML, CSV, XLSX) for professional review.</p>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      <button
        className="bg-slate-900 text-white px-3 py-2"
        onClick={async () => {
          try {
            const res = await api.post(`/projects/${projectId}/report/generate`);
            setMessage(res.data.disclaimer || 'Report exports generated.');
            refreshExports();
          } catch {
            setMessage('Failed to generate report exports.');
          }
        }}
      >
        Generate Draft Evidence Pack
      </button>
      {message && <p className="text-xs text-slate-700">{message}</p>}
      <div className="border rounded bg-white p-3">
        <p className="font-medium mb-2">Available exports</p>
        <ul className="list-disc pl-6 text-sm">
          {exportsList.map((e) => (
            <li key={e.id || `${e.type}-${e.path}`}>{e.type}: {e.path}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
