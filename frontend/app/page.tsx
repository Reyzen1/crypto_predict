import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendingUp, TrendingDown, Bitcoin, DollarSign, Target, Activity } from "lucide-react"

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-6xl font-bold text-white">
          AI-Powered Crypto
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            {" "}Predictions
          </span>
        </h1>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto">
          Leverage advanced machine learning to predict cryptocurrency prices with unprecedented accuracy
        </p>
        <div className="flex justify-center gap-4 mt-6">
          <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
            Get Started
          </Button>
          <Button size="lg" variant="outline" className="border-gray-600 text-gray-300">
            View Demo
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">
              Bitcoin Price
            </CardTitle>
            <Bitcoin className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">$43,234.56</div>
            <div className="flex items-center space-x-2 text-sm">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-green-500">+2.4%</span>
              <span className="text-gray-400">24h</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">
              Prediction Accuracy
            </CardTitle>
            <Target className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">87.3%</div>
            <div className="flex items-center space-x-2 text-sm">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-green-500">+1.2%</span>
              <span className="text-gray-400">this week</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">
              Active Predictions
            </CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">24</div>
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-gray-400">across 5 cryptocurrencies</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">
              Portfolio Value
            </CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">$12,456.78</div>
            <div className="flex items-center space-x-2 text-sm">
              <TrendingDown className="h-4 w-4 text-red-500" />
              <span className="text-red-500">-0.8%</span>
              <span className="text-gray-400">24h</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Features Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white">Latest Predictions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Bitcoin className="h-6 w-6 text-orange-500" />
                <div>
                  <div className="text-white font-medium">Bitcoin</div>
                  <div className="text-sm text-gray-400">24h prediction</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-white font-medium">$44,120.00</div>
                <Badge variant="outline" className="text-green-500 border-green-500">
                  High Confidence
                </Badge>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-6 w-6 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-white">E</span>
                </div>
                <div>
                  <div className="text-white font-medium">Ethereum</div>
                  <div className="text-sm text-gray-400">24h prediction</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-white font-medium">$2,456.78</div>
                <Badge variant="outline" className="text-yellow-500 border-yellow-500">
                  Medium Confidence
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white">Market Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center text-gray-400">
                <p>Real-time market data visualization will be displayed here</p>
                <p className="text-sm mt-2">Chart integration coming soon...</p>
              </div>
              <div className="h-48 bg-gray-700/30 rounded-lg flex items-center justify-center">
                <div className="text-gray-500">
                  <Activity className="h-12 w-12 mx-auto mb-2" />
                  <p>Chart Placeholder</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}