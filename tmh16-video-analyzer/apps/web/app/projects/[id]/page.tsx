'use client';
import { useParams } from 'next/navigation';

const pages = ['video-upload', 'scene-setup', 'detection-review', 'counts-dashboard', 'queue-dashboard', 'pedestrian-dashboard', 'school-mode-dashboard', 'parking-dashboard', 'report-generation'];

export default function ProjectDetail() {
  const params = useParams();
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Project {params.id}</h1>
      <p>Open analysis modules:</p>
      <ul className="list-disc pl-6">{pages.map(p => <li key={p}>{p}</li>)}</ul>
    </div>
  );
}
