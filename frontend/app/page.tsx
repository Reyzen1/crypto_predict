// File: frontend/app/page.tsx
// TEST VERSION - Chart Import Test

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  CheckCircle,
  AlertCircle,
  BarChart3,
  Loader2
} from "lucide-react";

// Test Chart Import
import PriceChart from '../components/charts/PriceChart';
import { testApiService } from '../lib/api';

export default function Dashboard() {
  const [importStatus, setImportStatus] = useState('testing');
  const [apiStatus, setApiStatus] = useState('testing');

  useEffect(() => {
    // Test imports
    setTimeout(() => {
      setImportStatus('success');
    }, 1000);

    // Test API
    setTimeout(() => {
      try {
        const testData = testApiService.getCurrentPrice();
        console.log('API Test:', testData);
        setApiStatus('success');
      } catch (error) {
        console.error('API Test Failed:', error);
        setApiStatus('error');
      }
    }, 1500);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-8 space-y-8">
        
        {/* Import Status Check */}
        <div className="bg-blue-500/20 border-2 border-blue-500 rounded-lg p-6">
          <h2 className="text-blue-400 text-2xl font-bold mb-4">
            🧪 Chart Import & Component Test
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Import Status */}
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                {importStatus === 'testing' ? (
                  <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                ) : importStatus === 'success' ? (
                  <CheckCircle className="h-5 w-5 text-green-400" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-400" />
                )}
                <div>
                  <p className="text-white font-medium">Component Import</p>
                  <p className="text-gray-400 text-sm">
                    {importStatus === 'testing' ? 'Testing...' :
                     importStatus === 'success' ? 'PriceChart.tsx imported successfully' :
                     'Import failed'}
                  </p>
                </div>
              </div>
            </div>

            {/* API Status */}
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                {apiStatus === 'testing' ? (
                  <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
                ) : apiStatus === 'success' ? (
                  <CheckCircle className="h-5 w-5 text-green-400" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-400" />
                )}
                <div>
                  <p className="text-white font-medium">API Service</p>
                  <p className="text-gray-400 text-sm">
                    {apiStatus === 'testing' ? 'Testing...' :
                     apiStatus === 'success' ? 'Mock API working' :
                     'API failed'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Hero Section */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-6xl font-bold text-white">
            Component Test
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              {" "}Dashboard
            </span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Testing chart component imports and file structure
          </p>
        </div>

        {/* Chart Component Test */}
        <div className="space-y-4">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-white mb-2">📊 Chart Component Test</h2>
            <p className="text-gray-400">
              If you see a success message below, the chart component is working!
            </p>
          </div>

          {/* This will test if PriceChart component renders */}
          {importStatus === 'success' ? (
            <PriceChart className="w-full" />
          ) : (
            <Card className="bg-gray-800/50 border-gray-700">
              <CardContent className="p-8">
                <div className="text-center">
                  <Loader2 className="h-12 w-12 text-blue-400 animate-spin mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-white mb-2">Loading Chart Component...</h3>
                  <p className="text-gray-400">Testing component import...</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Debug Info */}
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white">🔧 Debug Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-gray-400">Import Status:</span>
                <span className={`font-bold ${
                  importStatus === 'success' ? 'text-green-400' :
                  importStatus === 'error' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {importStatus.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Expected Path:</span>
                <span className="text-blue-400">../components/charts/PriceChart</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">API Service:</span>
                <span className={`font-bold ${
                  apiStatus === 'success' ? 'text-green-400' :
                  apiStatus === 'error' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {apiStatus.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Timestamp:</span>
                <span className="text-white">{new Date().toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Instructions */}
        <Card className="bg-amber-500/10 border-amber-500">
          <CardContent className="p-6">
            <h3 className="text-amber-400 font-bold text-lg mb-3">📋 Next Steps:</h3>
            <div className="space-y-2 text-amber-200 text-sm">
              <p>1. If you see "CHART COMPONENT LOADED SUCCESSFULLY" above, imports are working!</p>
              <p>2. If not, check these files exist:</p>
              <ul className="ml-4 space-y-1">
                <li>• <code>frontend/components/charts/PriceChart.tsx</code></li>
                <li>• <code>frontend/lib/api.ts</code></li>
              </ul>
              <p>3. Check browser console (F12) for any import errors</p>
              <p>4. Make sure you restarted <code>npm run dev</code> after creating files</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}