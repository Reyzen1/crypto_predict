// File: frontend/next.config.js
// Next.js configuration for CryptoPredict Frontend - Updated for Next.js 15+

/** @type {import('next').NextConfig} */
const nextConfig = {
  // API rewrites to proxy to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production' 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`
          : 'http://localhost:8000/api/:path*', // Docker backend URL
      },
    ];
  },

  // Environment variables
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Image domains for external images
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.coingecko.com',
      },
      {
        protocol: 'https',
        hostname: 'assets.coingecko.com',
      },
      {
        protocol: 'https',
        hostname: 'coin-images.coingecko.com',
      },
      {
        protocol: 'https',
        hostname: 's2.coinmarketcap.com',
      },
    ],
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          }
        ],
      },
    ];
  },

  // Webpack configuration
  webpack: (config, { dev, isServer }) => {
    // Handle SVG files
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    // Development-specific webpack config
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }

    return config;
  },

  // Compiler options (Next.js 15+ format)
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Performance optimizations
  poweredByHeader: false,
  
  // Compression
  compress: true,

  // Static optimization
  trailingSlash: false,

  // Output configuration
  output: 'standalone',

  // TypeScript configuration
  typescript: {
    // Don't allow production builds with TypeScript errors
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    // Don't allow production builds with ESLint errors
    ignoreDuringBuilds: false,
    dirs: ['app', 'src', 'components', 'lib', 'hooks'],
  },

  // Redirects
  async redirects() {
    return [
      // Add any redirects here if needed
    ];
  },

  // Experimental features (for Next.js 15+)
  experimental: {
    // Add any experimental features here if needed
    optimizePackageImports: ['lucide-react'],
  },

  // Bundle analyzer (optional - only in development)
  ...(process.env.ANALYZE === 'true' && {
    webpack: (config, { isServer }) => {
      if (!isServer) {
        const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
        config.plugins.push(
          new BundleAnalyzerPlugin({
            analyzerMode: 'browser',
            openAnalyzer: true,
          })
        );
      }
      return config;
    },
  }),
};

module.exports = nextConfig;