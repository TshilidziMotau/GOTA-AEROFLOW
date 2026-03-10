'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

const starterScene = {
  scale_m_per_px: 0.05,
  count_lines: [{ name: 'northbound_entry', p1: [120, 200], p2: [420, 200] }],
  queue_zones: [{ name: 'gate_queue_zone', polygon: [[100, 220], [380, 220], [380, 320], [100, 320]] }],
  pedestrian_lines: [{ name: 'school_crossing', p1: [200, 150], p2: [260, 360] }],
};

export default function SceneSetupPage() {
  const [projectId, setProjectId] = useState('1');
  const [jsonText, setJsonText] = useState(JSON.stringify(starterScene, null, 2));
  const [message, setMessage] = useState('');

  const loadScene = () => {
    api.get(`/projects/${projectId}/scene`).then((r) => {
      const config = r.data?.config || starterScene;
      setJsonText(JSON.stringify(config, null, 2));
    }).catch(() => setJsonText(JSON.stringify(starterScene, null, 2)));
  };

  useEffect(() => {
    loadScene();
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Scene Setup / Calibration</h1>
      <p className="text-sm text-slate-600">Define calibration and geometry (count lines, queue zones, pedestrian lines). Use JSON editor in this MVP phase.</p>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      <textarea className="border p-2 w-full h-80 font-mono text-xs" value={jsonText} onChange={(e) => setJsonText(e.target.value)} />
      <button
        className="bg-slate-900 text-white px-3 py-2"
        onClick={async () => {
          try {
            const config = JSON.parse(jsonText);
            await api.post(`/projects/${projectId}/scene`, { config });
            setMessage('Scene configuration saved.');
          } catch {
            setMessage('Invalid JSON or save failed.');
          }
        }}
      >
        Save Scene Configuration
      </button>
      {message && <p className="text-xs text-slate-700">{message}</p>}
    </div>
  );
}
