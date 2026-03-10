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
  const projectId = params.id;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Project {projectId}</h1>
      <p>Open analysis modules:</p>
      <ul className="list-disc pl-6 space-y-1">
        {pages.map((page) => (
          <li key={page}>
            <Link className="text-blue-700 hover:underline" href={`/${page}?projectId=${encodeURIComponent(projectId)}`}>
              {page}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
