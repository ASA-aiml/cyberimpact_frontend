"use client";
import React, { useState } from "react";
import axios from "axios";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [runningCheck, setRunningCheck] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [checkResult, setCheckResult] = useState<any>(null);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const analyzeRepo = async () => {
    setAnalyzing(true);
    setAnalysisResult(null);
    setCheckResult(null);
    setError(null);
    try {
      const resp = await axios.post("http://localhost:8000/scan/analyze", {
        repo_url: repoUrl
      });
      setAnalysisResult(resp.data);
      setSelectedTools(resp.data.suggested_tools || []);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const runSecurityCheck = async () => {
    setRunningCheck(true);
    setCheckResult(null);
    setError(null);
    try {
      const resp = await axios.post("http://localhost:8000/scan/execute", {
        repo_path: analysisResult.repo_path,
        selected_tools: selectedTools
      });
      setCheckResult(resp.data);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setRunningCheck(false);
    }
  };

  const toggleTool = (tool: string) => {
    if (selectedTools.includes(tool)) {
      setSelectedTools(selectedTools.filter(t => t !== tool));
    } else {
      setSelectedTools([...selectedTools, tool]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 flex flex-col items-center p-8">
      <div className="w-full max-w-3xl">

        {/* Header */}
        <h1 className="text-4xl font-extrabold mb-4 text-white tracking-tight">
          🔍 AI-Powered Security Scanner
        </h1>
        <p className="text-gray-400 mb-8">
          Analyze GitHub repositories with Gemini AI and run targeted security checks.
        </p>

        {/* Card */}
        <div className="bg-gray-900/60 backdrop-blur-md shadow-xl rounded-xl border border-gray-800 p-6 space-y-6">

          {/* GitHub URL */}
          <div>
            <label className="block text-sm mb-2 font-semibold text-gray-300">
              GitHub Repository URL
            </label>
            <div className="flex gap-2">
              <input
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
                className="flex-1 rounded-lg bg-gray-800 text-gray-100 px-4 py-2 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={analyzeRepo}
                disabled={analyzing || !repoUrl}
                className={`px-6 py-2 rounded-lg font-semibold transition 
                  ${analyzing || !repoUrl
                    ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 text-white"}
                `}
              >
                {analyzing ? "Analyzing..." : "Analyze"}
              </button>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-900/50 border border-red-800 rounded-lg text-red-200">
              Error: {error}
            </div>
          )}

          {/* Analysis Results & Tool Selection */}
          {analysisResult && (
            <div className="animate-fade-in">
              <div className="mb-4 p-4 bg-blue-900/20 border border-blue-800 rounded-lg">
                <h3 className="text-lg font-semibold text-blue-200 mb-2">Analysis Complete</h3>
                <p className="text-sm text-gray-300">
                  Repository cloned to: <code className="bg-gray-800 px-1 rounded">{analysisResult.repo_path}</code>
                </p>
              </div>

              <label className="block text-sm mb-3 font-semibold text-gray-300">
                Suggested Tools (Select to run)
              </label>
              <div className="flex flex-wrap gap-3 mb-6">
                {selectedTools.map((tool) => (
                  <label
                    key={tool}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition
                      ${selectedTools.includes(tool)
                        ? "bg-blue-900/40 border-blue-500 text-blue-100"
                        : "bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700"}
                    `}
                  >
                    <input
                      type="checkbox"
                      checked={selectedTools.includes(tool)}
                      onChange={() => toggleTool(tool)}
                      className="accent-blue-500"
                    />
                    <span className="capitalize">{tool}</span>
                  </label>
                ))}
                {selectedTools.length === 0 && (
                  <p className="text-gray-500 italic">No specific tools suggested.</p>
                )}
              </div>

              <button
                onClick={runSecurityCheck}
                disabled={runningCheck || selectedTools.length === 0}
                className={`w-full py-3 rounded-lg text-lg font-semibold transition 
                  ${runningCheck || selectedTools.length === 0
                    ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                    : "bg-green-600 hover:bg-green-700 text-white"}
                `}
              >
                {runningCheck ? "Running Security Checks..." : "Run Security Check"}
              </button>
            </div>
          )}
        </div>

        {/* Check Results */}
        {checkResult && (
          <div className="mt-10 animate-fade-in">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-2xl font-bold">Security Report</h3>
              {checkResult.report_url && (
                <a
                  href={`http://localhost:8000${checkResult.report_url}`}
                  download
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2"
                >
                  📄 Download Report (DOCX)
                </a>
              )}
            </div>

            {/* AI Summary */}
            {checkResult.ai_summary && (
              <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-xl border border-purple-500/30 p-6 mb-8">
                <h4 className="text-xl font-bold text-purple-300 mb-3 flex items-center gap-2">
                  ✨ AI Executive Summary
                </h4>
                <div className="prose prose-invert max-w-none text-gray-200 whitespace-pre-wrap">
                  {checkResult.ai_summary}
                </div>
              </div>
            )}

            <div className="space-y-4">
              {Object.entries(checkResult.results).map(([tool, result]: [string, any]) => (
                <div key={tool} className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                  <div className="bg-gray-800/50 px-6 py-3 border-b border-gray-800">
                    <h4 className="font-bold text-lg capitalize text-blue-300">{tool}</h4>
                  </div>
                  <div className="p-6">
                    {result.error ? (
                      <p className="text-red-400">Error: {result.error}</p>
                    ) : (
                      <pre className="text-sm text-gray-300 whitespace-pre-wrap overflow-auto max-h-96">
                        {typeof result.output === 'string'
                          ? result.output
                          : JSON.stringify(result.output, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
