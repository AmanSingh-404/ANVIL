import { Space_Grotesk, IBM_Plex_Mono } from 'next/font/google';
import './globals.css';

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-space-grotesk',
});

const plexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-plex-mono',
});

export const metadata = {
  title: 'ANVIL — An agent that forges its own tools',
  description: 'A self-extending AI agent that writes, tests, reviews, and keeps its own tools.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body className={`${spaceGrotesk.variable} ${plexMono.variable}`}>
        {children}
      </body>
    </html>
  );
}