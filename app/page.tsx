"use client"

import type React from "react"

import { useState } from "react"
import { Shield, AlertTriangle, CheckCircle, Chrome, Download, Github, Zap, Globe, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface CheckResult {
  url: string
  prediction: string
  risk_score: number
  reasons: string[]
  safe: boolean
  timestamp?: string
}

export default function Dashboard() {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CheckResult | null>(null)
  const [error, setError] = useState("")

  const checkURL = async () => {
    if (!url.trim()) {
      setError("Please enter a URL")
      return
    }

    setLoading(true)
    setError("")
    setResult(null)

    try {
      const response = await fetch("http://localhost:5000/api/check-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: url.trim() }),
      })

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError("Failed to check URL. Make sure the backend API is running on http://localhost:5000")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      checkURL()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">PhishBlocker</h1>
              <p className="text-xs text-gray-600">AI-Powered Protection</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" asChild>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer">
                <Github className="w-4 h-4 mr-2" />
                GitHub
              </a>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            <span>Powered by Machine Learning</span>
          </div>
          <h2 className="text-5xl font-bold text-gray-900 mb-6">{"Stop Phishing Attacks Before They Start"}</h2>
          <p className="text-xl text-gray-600 mb-12">
            {
              "Protect yourself from malicious websites with our AI-powered detection system. Real-time protection across all your browsers."
            }
          </p>

          {/* URL Checker */}
          <Card className="shadow-xl border-2">
            <CardHeader>
              <CardTitle className="text-2xl">Check Any URL</CardTitle>
              <CardDescription>{"Enter a URL to analyze it for phishing threats"}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-6">
                <Input
                  type="url"
                  placeholder="https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="text-lg"
                />
                <Button
                  onClick={checkURL}
                  disabled={loading}
                  size="lg"
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Checking...
                    </>
                  ) : (
                    <>
                      <Shield className="w-4 h-4 mr-2" />
                      Check URL
                    </>
                  )}
                </Button>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {result && (
                <div
                  className={`p-6 rounded-lg border-2 ${
                    result.safe ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
                  }`}
                >
                  <div className="flex items-center gap-3 mb-4">
                    {result.safe ? (
                      <>
                        <CheckCircle className="w-8 h-8 text-green-600" />
                        <div className="text-left">
                          <h3 className="text-xl font-bold text-green-900">Safe Website</h3>
                          <p className="text-green-700">{"This URL appears to be legitimate"}</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-8 h-8 text-red-600" />
                        <div className="text-left">
                          <h3 className="text-xl font-bold text-red-900">Phishing Detected!</h3>
                          <p className="text-red-700">{"This website may be dangerous"}</p>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="bg-white/60 rounded-lg p-4 mb-4">
                    <div className="text-sm text-gray-600 mb-1">Risk Score</div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            result.risk_score > 70
                              ? "bg-red-600"
                              : result.risk_score > 40
                                ? "bg-yellow-600"
                                : "bg-green-600"
                          }`}
                          style={{ width: `${result.risk_score}%` }}
                        />
                      </div>
                      <span className="text-2xl font-bold text-gray-900">{result.risk_score.toFixed(1)}%</span>
                    </div>
                  </div>

                  {result.reasons.length > 0 && (
                    <div className="bg-white/60 rounded-lg p-4 text-left">
                      <h4 className="font-semibold text-gray-900 mb-2">Detection Reasons:</h4>
                      <ul className="space-y-1">
                        {result.reasons.map((reason, idx) => (
                          <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="text-gray-400">•</span>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">{"Why Choose PhishBlocker?"}</h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-3">
                <Zap className="w-6 h-6 text-indigo-600" />
              </div>
              <CardTitle>{"AI-Powered Detection"}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                {
                  "Advanced machine learning models trained on millions of URLs to identify phishing patterns with high accuracy."
                }
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-3">
                <Globe className="w-6 h-6 text-purple-600" />
              </div>
              <CardTitle>{"Real-Time Protection"}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                {"Get instant alerts as you browse. Our extension checks every website you visit in real-time."}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="w-12 h-12 bg-pink-100 rounded-lg flex items-center justify-center mb-3">
                <Lock className="w-6 h-6 text-pink-600" />
              </div>
              <CardTitle>{"Privacy First"}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                {"Your browsing data stays private. We only analyze URLs, not your personal information."}
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Extensions Download */}
      <section className="container mx-auto px-4 py-16 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-3xl text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">{"Install Browser Extension"}</h2>
          <p className="text-xl text-indigo-100 mb-12">
            {"Get real-time protection while browsing. Available for all major browsers."}
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            <Card className="border-2 border-white/20 bg-white/10 backdrop-blur-sm text-white">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <Chrome className="w-8 h-8" />
                  <CardTitle className="text-2xl">Chrome / Brave / Edge</CardTitle>
                </div>
                <CardDescription className="text-indigo-100">{"Chromium-based browsers"}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="secondary" size="lg" className="w-full" asChild>
                  <a href="/extensions/chrome" download>
                    <Download className="w-4 h-4 mr-2" />
                    Download Extension
                  </a>
                </Button>
                <p className="text-sm text-indigo-100 mt-4">{"Load unpacked extension from chrome://extensions"}</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-white/20 bg-white/10 backdrop-blur-sm text-white">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <Globe className="w-8 h-8" />
                  <CardTitle className="text-2xl">Firefox</CardTitle>
                </div>
                <CardDescription className="text-indigo-100">{"Mozilla Firefox browser"}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="secondary" size="lg" className="w-full" asChild>
                  <a href="/extensions/firefox" download>
                    <Download className="w-4 h-4 mr-2" />
                    Download Extension
                  </a>
                </Button>
                <p className="text-sm text-indigo-100 mt-4">{"Load temporary add-on from about:debugging"}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-12 text-center text-gray-600">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-indigo-600" />
          <span className="font-semibold text-gray-900">PhishBlocker</span>
        </div>
        <p className="text-sm">{"Protected by AI-powered phishing detection • Built with Next.js & Python"}</p>
        <p className="text-xs mt-2">{"© 2025 PhishBlocker. All rights reserved."}</p>
      </footer>
    </div>
  )
}
