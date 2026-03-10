'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../../lib/api';

export default function ProjectsPage() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { api.get('/projects').then(r => setItems(r.data)); }, []);
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Projects</h1>
      {items.map((p) => <Link className="block underline" key={p.id} href={`/projects/${p.id}`}>{p.name}</Link>)}
    </div>
  );
}
