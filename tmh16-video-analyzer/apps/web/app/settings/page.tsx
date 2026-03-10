'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function SettingsPage() {
  const [profile, setProfile] = useState<any>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.get('/auth/me')
      .then((r) => setProfile(r.data))
      .catch(() => setMessage('Not authenticated. Please sign in.'));
  }, []);

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Settings</h1>
      {profile ? (
        <div className="border rounded bg-white p-3 text-sm">
          <p>Email: <strong>{profile.email}</strong></p>
          <p>Role: <strong>{profile.role}</strong></p>
        </div>
      ) : (
        <p className="text-sm text-slate-600">{message}</p>
      )}
      <button
        className="border px-3 py-2"
        onClick={() => {
          window.localStorage.removeItem('tmh16_token');
          window.localStorage.removeItem('tmh16_role');
          setProfile(null);
          setMessage('Signed out.');
        }}
      >
        Sign out
      </button>
    </div>
  );
}
