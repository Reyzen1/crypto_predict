import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CryptoPredict MVP',
  description: 'AI-powered cryptocurrency price prediction platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
          <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-white">
                  CryptoPredict
                </h1>
                <nav className="flex space-x-6">
                  <a href="/" className="text-gray-300 hover:text-white transition-colors">
                    Dashboard
                  </a>
                  <a href="/predictions" className="text-gray-300 hover:text-white transition-colors">
                    Predictions
                  </a>
                  <a href="/portfolio" className="text-gray-300 hover:text-white transition-colors">
                    Portfolio
                  </a>
                </nav>
              </div>
            </div>
          </header>
          
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          
          <footer className="border-t border-gray-800 bg-gray-900/50 backdrop-blur-sm mt-12">
            <div className="container mx-auto px-4 py-6">
              <div className="text-center text-gray-400">
                <p>&copy; 2024 CryptoPredict MVP. All rights reserved.</p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}