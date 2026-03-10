'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api, formatApiError } from '../../lib/api';
import axios from 'axios';
import { api } from '../../lib/api';

type Project = { id: number; name: string };

export default function VideoUploadPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState('');
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function VideoUploadPage() {
  const [projectId, setProjectId] = useState('1');
  const [file, setFile] = useState<File | null>(null);
  const [videos, setVideos] = useState<any[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api
      .get('/projects')
      .then((r) => {
        const rows = (r.data || []) as Project[];
        setProjects(rows);
        if (!projectId && rows.length > 0) {
          setProjectId(String(rows[0].id));
        }
      })
      .catch(() => {
        setProjects([]);
      });
  }, []);

  const selectedProject = useMemo(() => projects.find((p) => String(p.id) === projectId) || null, [projects, projectId]);

  const loadVideos = () => {
    if (!projectId) {
      setVideos([]);
      return;
    }
    api
      .get(`/projects/${projectId}/videos`)
      .then((r) => setVideos(r.data || []))
      .catch(() => setVideos([]));
  const loadVideos = () => {
    api.get(`/projects/${projectId}/videos`).then((r) => setVideos(r.data)).catch(() => setVideos([]));
  };

  useEffect(() => {
    loadVideos();
  }, [projectId]);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Video Upload</h1>
      <p className="text-sm text-slate-600">Upload Phantom 4 Pro `.mp4` files and review captured metadata for analysis setup.</p>

      {projects.length === 0 ? (
        <div className="border rounded bg-white p-3 text-sm space-y-2">
          <p>No projects found yet.</p>
          <Link className="underline text-blue-700" href="/projects/new">
            Create a project first
          </Link>
        </div>
      ) : (
        <>
          <label className="text-sm">
            Project
            <select className="border p-2 ml-2" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (#{p.id})
                </option>
              ))}
            </select>
          </label>

          <input type="file" accept="video/mp4" onChange={(e) => setFile(e.target.files?.[0] || null)} />

          <button
            className="bg-slate-900 text-white px-3 py-2"
            onClick={async () => {
              if (!projectId) {
                setMessage('Select a project first.');
                return;
              }
              if (!file) {
                setMessage('Choose an MP4 file first.');
                return;
              }
              const formData = new FormData();
              formData.append('file', file);
              try {
                const res = await api.post(`/projects/${projectId}/videos`, formData, {
                  headers: { 'Content-Type': 'multipart/form-data' },
                });
                setMessage(`Uploaded to ${selectedProject?.name || `project ${projectId}`}: ${res.data.video_path}`);
                loadVideos();
              } catch (err) {
                setMessage(`Upload failed ${formatApiError(err)}`);
                if (axios.isAxiosError(err)) {
                  const detail = (err.response?.data as any)?.detail;
                  setMessage(`Upload failed (${err.response?.status || 'network'}): ${detail || err.message}`);
                } else {
                  setMessage('Upload failed due to an unexpected error.');
                }
              }
            }}
          >
            Upload Video
          </button>
        </>
      )}

      {message && <p className="text-xs text-slate-700">{message}</p>}

      <div className="border rounded bg-white p-3">
        <p className="font-medium mb-2">Project videos</p>
        {selectedProject && <p className="text-xs text-slate-600 mb-2">Showing videos for: {selectedProject.name}</p>}
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />
      <input type="file" accept="video/mp4" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button
        className="bg-slate-900 text-white px-3 py-2"
        onClick={async () => {
          if (!file) {
            setMessage('Choose an MP4 file first.');
            return;
          }
          const formData = new FormData();
          formData.append('file', file);
          try {
            const res = await api.post(`/projects/${projectId}/videos`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
            });
            setMessage(`Uploaded: ${res.data.video_path}`);
            loadVideos();
          } catch {
            setMessage('Upload failed. Confirm API is running and project exists.');
          }
        }}
      >
        Upload Video
      </button>
      {message && <p className="text-xs text-slate-700">{message}</p>}
      <div className="border rounded bg-white p-3">
        <p className="font-medium mb-2">Project videos</p>
        <ul className="list-disc pl-6 text-sm">
          {videos.map((v) => (
            <li key={v.id}>
              {v.filename} · {v.resolution || 'n/a'} · {v.fps ? Number(v.fps).toFixed(2) : 'n/a'} fps · {v.duration_s ? Number(v.duration_s).toFixed(1) : 'n/a'} s
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
