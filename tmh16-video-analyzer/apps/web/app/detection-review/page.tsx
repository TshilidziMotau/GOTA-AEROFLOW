'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function DetectionReviewPage() {
  const [projectId, setProjectId] = useState('1');
  const [tracks, setTracks] = useState<any[]>([]);
  const [edits, setEdits] = useState<any[]>([]);
  const [message, setMessage] = useState('');

  const load = () => {
    api.get(`/projects/${projectId}/tracks`).then((r) => setTracks(r.data)).catch(() => setTracks([]));
    api.get(`/projects/${projectId}/manual-edits`).then((r) => setEdits(r.data)).catch(() => setEdits([]));
  };

  useEffect(() => {
    load();
  }, [projectId]);

  const postEdit = async (edit_type: string, payload: any) => {
    try {
      await api.post(`/projects/${projectId}/manual-corrections`, { edit_type, payload });
      setMessage(`Applied ${edit_type}`);
      load();
    } catch {
      setMessage(`Failed ${edit_type}`);
    }
  };

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Detection Review</h1>
      <p className="text-sm text-slate-600">Review auto-tracked objects, apply manual corrections, and inspect audit trail.</p>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      {message && <p className="text-xs text-slate-700">{message}</p>}

      <div className="border rounded bg-white p-3">
        <p className="text-sm font-medium mb-2">Latest tracks: {tracks.length}</p>
        <div className="space-y-1 max-h-72 overflow-auto text-xs">
          {tracks.map((t, i) => (
            <div key={t.id} className="border p-2 rounded space-y-1">
              <div>#{t.id} · {t.object_class} · frames {t.start_frame}-{t.end_frame}</div>
              <div className="flex gap-2 flex-wrap">
                <button className="border px-2 py-1" onClick={() => postEdit('reclassify_track', { track_id: t.id, new_class: 'car' })}>Set Car</button>
                <button className="border px-2 py-1" onClick={() => postEdit('reclassify_track', { track_id: t.id, new_class: 'pedestrian' })}>Set Ped</button>
                <button className="border px-2 py-1" onClick={() => postEdit('delete_track', { track_id: t.id })}>Delete</button>
                {i > 0 && <button className="border px-2 py-1" onClick={() => postEdit('merge_tracks', { source_track_id: t.id, target_track_id: tracks[i - 1].id })}>Merge Prev</button>}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="border rounded bg-white p-3">
        <p className="text-sm font-medium mb-2">Manual edit audit trail</p>
        <div className="space-y-1 max-h-56 overflow-auto text-xs">
          {edits.map((e) => (
            <div key={e.id} className="border p-2 rounded">
              #{e.id} · {e.edit_type} · user {e.user_id}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
