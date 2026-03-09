import './globals.css';
import { Nav } from '../components/nav';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
