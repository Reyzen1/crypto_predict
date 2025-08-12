// File: frontend/app/layout.tsx
// Enhanced Layout - Temporarily without AuthProvider

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

// Temporarily comment out AuthProvider import
// import { AuthProvider } from '@/contexts/AuthContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'CryptoPredict - Free AI Crypto Analysis',
  description: 'Complete cryptocurrency analysis platform with AI predictions, technical analysis, and real-time data. 100% free for everyone.',
  keywords: 'cryptocurrency, bitcoin, AI prediction, technical analysis, free crypto tools',
  openGraph: {
    title: 'CryptoPredict - Free AI Crypto Analysis',
    description: 'Complete cryptocurrency analysis platform with AI predictions, technical analysis, and real-time data. 100% free for everyone.',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Temporarily render children directly without AuthProvider */}
        {children}
      </body>
    </html>
  );
}