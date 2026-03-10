import Link from 'next/link';

const links = [
  ['Dashboard', '/dashboard'],
  ['Projects', '/projects'],
  ['New Project', '/projects/new'],
  ['Settings', '/settings'],
] as const;

export function Nav() {
  return (
    <nav className="flex gap-4 p-4 border-b bg-white">
      {links.map(([label, href]) => (
        <Link className="text-sm font-medium text-slate-700 hover:text-slate-950" key={href} href={href}>{label}</Link>
      ))}
    </nav>
  );
}
