import Link from 'next/link';

const pages = [
  'video-upload',
  'scene-setup',
  'detection-review',
  'counts-dashboard',
  'queue-dashboard',
  'pedestrian-dashboard',
  'school-mode-dashboard',
  'parking-dashboard',
  'report-generation',
] as const;

type ProjectDetailProps = {
  params: {
    id: string;
  };
};

export default function ProjectDetail({ params }: ProjectDetailProps) {
'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

const pages = ['video-upload', 'scene-setup', 'detection-review', 'counts-dashboard', 'queue-dashboard', 'pedestrian-dashboard', 'school-mode-dashboard', 'parking-dashboard', 'report-generation'] as const;

export default function ProjectDetail() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Project {projectId}</h1>
      <p>Open analysis modules:</p>
      <ul className="list-disc pl-6 space-y-1">
        {pages.map((page) => (
          <li key={page}>
            <Link className="text-blue-700 hover:underline" href={`/${page}?projectId=${encodeURIComponent(projectId)}`}>
            <Link className="text-blue-700 hover:underline" href={`/${page}?projectId=${projectId}`}>
              {page}
            </Link>
          </li>
        ))}
      </ul>
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
