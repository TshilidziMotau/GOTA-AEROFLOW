'use client';
import { useState } from 'react';
import { api } from '../../lib/api';

export default function LoginPage() {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [message, setMessage] = useState('');

  return (
    <div className="max-w-md space-y-3">
      <h1 className="text-xl font-semibold">Login</h1>
      <input className="border p-2 w-full" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input className="border p-2 w-full" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button className="bg-slate-900 text-white px-3 py-2" onClick={async () => {
        try {
          const res = await api.post('/auth/login', { email, password });
          window.localStorage.setItem('tmh16_token', res.data.access_token);
          window.localStorage.setItem('tmh16_role', res.data.role);
          setMessage(`Signed in as ${res.data.role}. Token stored for API calls.`);
        } catch {
          setMessage('Login failed. Check credentials.');
        }
      }}>Sign in</button>
      {message && <p className="text-xs break-all">{message}</p>}
    </div>
  );
}
