'use client';
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
