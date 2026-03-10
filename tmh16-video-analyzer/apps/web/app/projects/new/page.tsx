'use client';

import Link from 'next/link';
import { useState } from 'react';
import { api, formatApiError } from '../../../lib/api';

const initial = {
  name: '',
  site_name: '',
  site_type: 'school',
  location: '',
  survey_date: '',
  survey_period: '',
  notes: '',
};

export default function NewProjectPage() {
  const [form, setForm] = useState(initial);
  const [message, setMessage] = useState('');
  const [creating, setCreating] = useState(false);

  const canCreate = form.name.trim().length > 0;

  return (
    <div className="space-y-3 max-w-xl">
      <h1 className="text-xl font-semibold">New Project</h1>
      <p className="text-sm text-slate-600">You must be signed in as an admin or analyst to create a project.</p>
      <p className="text-xs">
        Need to sign in?{' '}
        <Link className="underline text-blue-700" href="/login">
          Go to login
        </Link>
      </p>

      {Object.keys(initial).map((k) => (
        <input
          key={k}
          className="border p-2 w-full"
          placeholder={k}
          value={(form as any)[k]}
          onChange={(e) => setForm({ ...form, [k]: e.target.value })}
        />
      ))}

      <button
        className="bg-slate-900 text-white px-3 py-2 disabled:opacity-50"
        disabled={!canCreate || creating}
        onClick={async () => {
          if (!canCreate) {
            setMessage('Project name is required.');
            return;
          }
          setCreating(true);
          setMessage('');
          try {
            const res = await api.post('/projects', form);
            setMessage(`Project created: ${res.data.name} (#${res.data.id}).`);
            setForm(initial);
          } catch (err) {
            setMessage(`Create failed ${formatApiError(err)}. Ensure you are logged in with admin/analyst role.`);
          } finally {
            setCreating(false);
          }
        }}
      >
        {creating ? 'Creating...' : 'Create'}
      </button>

      {message && <p className="text-xs text-slate-700">{message}</p>}
import { useState } from 'react';
import { api } from '../../../lib/api';

const initial = { name: '', site_name: '', site_type: 'school', location: '', survey_date: '', survey_period: '', notes: '' };

export default function NewProjectPage() {
  const [form, setForm] = useState(initial);
  return (
    <div className="space-y-3 max-w-xl">
      <h1 className="text-xl font-semibold">New Project</h1>
      {Object.keys(initial).map((k) => (
        <input key={k} className="border p-2 w-full" placeholder={k} value={(form as any)[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
      ))}
      <button className="bg-slate-900 text-white px-3 py-2" onClick={() => api.post('/projects', form)}>Create</button>
    </div>
  );
}
