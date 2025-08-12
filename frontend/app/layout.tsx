// File: frontend/app/layout.tsx
// Enhanced Layout with proper AuthProvider integration

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

// Import AuthProvider and ToastProvider
import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider } from '@/components/ToastProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'CryptoPredict - Free AI Crypto Analysis',
  description: 'Complete cryptocurrency analysis platform with AI predictions, technical analysis, and real-time data. 100% free for everyone.',
  keywords: 'cryptocurrency, bitcoin, AI prediction, technical analysis, free crypto tools',
  openGraph: {
    title: 'CryptoPredict - Free AI Crypto Analysis',
    description: 'Complete cryptocurrency analysis platform with AI predictions, technical analysis, and real-time data. 100% free for everyone.',
    type: 'website',
    url: 'https://cryptopredict.app',
    siteName: 'CryptoPredict',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CryptoPredict - Free AI Crypto Analysis',
    description: 'Complete cryptocurrency analysis platform with AI predictions, technical analysis, and real-time data. 100% free for everyone.',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://api.coingecko.com" />
        <link rel="preconnect" href="https://api.binance.com" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <meta name="theme-color" content="#1f2937" />
      </head>
      <body className={`${inter.className} bg-gray-900 text-white antialiased`}>
        <AuthProvider>
          <ToastProvider>
            <div className="min-h-screen flex flex-col">
              {children}
            </div>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}