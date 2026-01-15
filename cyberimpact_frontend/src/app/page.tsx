"use client";
import React, { useState } from "react";
import axios from "axios";
import Login from "../components/Login";
import AssetInventoryUpload from "../components/AssetInventoryUpload";
import FinancialDocUpload from "../components/FinancialDocUpload";
import { useUser } from "@/contexts/UserContext";

export default function Home() {
  const { idToken } = useUser(); // Get Firebase ID token from context
  const [activeTab, setActiveTab] = useState<'scanner' | 'uploads'>('scanner');
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

    // Check if user is authenticated
    if (!idToken) {
      setError("Please sign in with Google to run security scans");
      setRunningCheck(false);
      return;
    }

    try {
      const resp = await axios.post(
        "http://localhost:8000/scan/execute",
        {
          repo_path: analysisResult.repo_path,
          selected_tools: selectedTools
        },
        {
          headers: {
            Authorization: `Bearer ${idToken}` // Include Firebase token
          }
        }
      );
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
        <Login />
        {/* Header */}
        <h1 className="text-4xl font-extrabold mb-4 text-white tracking-tight">
          🔍 CyberImpact Platform
        </h1>
        <p className="text-gray-400 mb-8">
          Security scanning and document management platform powered by AI.
        </p>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('scanner')}
            className={`px-6 py-3 rounded-lg font-semibold transition ${activeTab === 'scanner'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
          >
            🔒 Security Scanner
          </button>
          <button
            onClick={() => setActiveTab('uploads')}
            className={`px-6 py-3 rounded-lg font-semibold transition ${activeTab === 'uploads'
              ? 'bg-green-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
          >
            📁 Document Uploads
          </button>
        </div>

        {/* Scanner Tab */}
        {activeTab === 'scanner' && (
          <>
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

                {/* Financial Analysis Summary */}
                {checkResult.financial_analysis && (
                  <>
                    <div className="bg-gradient-to-r from-green-900/50 to-emerald-900/50 rounded-xl border border-green-500/30 p-6 mb-8">
                      <h4 className="text-xl font-bold text-green-300 mb-4 flex items-center gap-2">
                        💰 Financial Impact Analysis
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-black/30 rounded-lg p-4">
                          <p className="text-xs text-gray-400 uppercase mb-1">Total Exposure</p>
                          <p className="text-2xl font-bold text-red-400">
                            ${(checkResult.financial_analysis.summary.total_financial_exposure / 1000000).toFixed(2)}M
                          </p>
                        </div>
                        <div className="bg-black/30 rounded-lg p-4">
                          <p className="text-xs text-gray-400 uppercase mb-1">Fix Cost</p>
                          <p className="text-2xl font-bold text-blue-400">
                            ${(checkResult.financial_analysis.summary.total_fix_cost / 1000).toFixed(0)}K
                          </p>
                        </div>
                        <div className="bg-black/30 rounded-lg p-4">
                          <p className="text-xs text-gray-400 uppercase mb-1">Avg ROSI</p>
                          <p className="text-2xl font-bold text-green-400">
                            {checkResult.financial_analysis.summary.average_rosi.toFixed(0)}%
                          </p>
                        </div>
                        <div className="bg-black/30 rounded-lg p-4">
                          <p className="text-xs text-gray-400 uppercase mb-1">Risk Tickets</p>
                          <p className="text-2xl font-bold text-yellow-400">
                            {checkResult.financial_analysis.risk_tickets_count}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 text-sm text-gray-300">
                        <p>✅ {checkResult.financial_analysis.assets_mapped} of {checkResult.financial_analysis.vulnerabilities_processed} vulnerabilities mapped to business assets</p>
                      </div>
                    </div>

                    {/* Download Full Report Button */}
                    <div className="mb-6 text-center">
                      <p className="text-gray-400 mb-2">For complete financial risk tickets with detailed calculations:</p>
                      {checkResult.report_url && (
                        <a
                          href={`http://localhost:8000${checkResult.report_url}`}
                          download
                          className="inline-flex items-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-3 rounded-lg font-semibold shadow-lg"
                        >
                          📊 Download Complete Financial Report
                        </a>
                      )}
                    </div>

                    {/* Detailed Risk Tickets */}
                    {checkResult.financial_analysis.top_risk_tickets && checkResult.financial_analysis.top_risk_tickets.length > 0 && (
                      <div className="mb-8">
                        <h4 className="text-2xl font-bold text-white mb-4">🎫 Top Financial Risk Tickets</h4>
                        <p className="text-gray-400 mb-6">Showing top {checkResult.financial_analysis.top_risk_tickets.length} vulnerabilities by financial impact</p>

                        <div className="space-y-6">
                          {checkResult.financial_analysis.top_risk_tickets.map((ticket: any, index: number) => (
                            <div key={index} className="bg-gray-900 rounded-xl border-2 border-gray-800 overflow-hidden hover:border-gray-700 transition">
                              {/* Ticket Header */}
                              <div className={`px-6 py-4 border-b-2 ${ticket.severity.toUpperCase() === 'CRITICAL' ? 'bg-red-900/30 border-red-800' :
                                  ticket.severity.toUpperCase() === 'HIGH' ? 'bg-orange-900/30 border-orange-800' :
                                    ticket.severity.toUpperCase() === 'MEDIUM' ? 'bg-yellow-900/30 border-yellow-800' :
                                      'bg-blue-900/30 border-blue-800'
                                }`}>
                                <div className="flex justify-between items-start">
                                  <div>
                                    <h5 className="text-xl font-bold text-white flex items-center gap-2">
                                      {ticket.severity_emoji} Risk Ticket #{ticket.ticket_number}
                                    </h5>
                                    <p className="text-sm text-gray-300 mt-1">
                                      <span className="font-semibold">Asset:</span> {ticket.asset_name}
                                    </p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-xs text-gray-400 uppercase">Total Exposure</p>
                                    <p className="text-2xl font-bold text-red-400">
                                      ${(ticket.financial_exposure.total / 1000000).toFixed(2)}M
                                    </p>
                                  </div>
                                </div>
                              </div>

                              {/* Ticket Body */}
                              <div className="p-6 space-y-6">
                                {/* Executive Summary */}
                                <div>
                                  <h6 className="text-sm font-bold text-purple-300 uppercase mb-2">👔 Executive Summary</h6>
                                  <p className="text-gray-300 text-sm leading-relaxed">{ticket.executive_summary}</p>
                                </div>

                                {/* Financial Breakdown - THE DETAILED CALCULATIONS */}
                                <div className="bg-black/40 rounded-lg p-4 border border-gray-800">
                                  <h6 className="text-sm font-bold text-green-300 uppercase mb-3">💰 Financial Calculation Breakdown</h6>

                                  <div className="space-y-3 text-sm">
                                    {/* Step 1: Direct Loss */}
                                    <div className="border-l-4 border-blue-500 pl-4">
                                      <p className="text-gray-400 mb-1">Step 1: Direct Downtime Cost</p>
                                      <p className="text-white font-mono">
                                        Direct Loss = Hourly Cost × RTO
                                      </p>
                                      <p className="text-gray-300 mt-1">
                                        = ${ticket.financial_exposure.direct_loss.toLocaleString()}
                                      </p>
                                    </div>

                                    {/* Step 2: Indirect Costs */}
                                    <div className="border-l-4 border-yellow-500 pl-4">
                                      <p className="text-gray-400 mb-1">Step 2: Indirect Costs (Reputation, Churn)</p>
                                      <p className="text-white font-mono">
                                        Indirect Loss = Direct Loss / 0.04 - Direct Loss
                                      </p>
                                      <p className="text-gray-300 mt-1">
                                        = ${ticket.financial_exposure.indirect_loss.toLocaleString()}
                                        <span className="text-gray-500 ml-2">(96% of total impact)</span>
                                      </p>
                                    </div>

                                    {/* Step 3: Breach Penalty */}
                                    {ticket.financial_exposure.breach_penalty > 0 && (
                                      <div className="border-l-4 border-red-500 pl-4">
                                        <p className="text-gray-400 mb-1">Step 3: Data Breach Penalty</p>
                                        <p className="text-white font-mono">
                                          PCI/PII Breach Penalty = $1,000,000
                                        </p>
                                        <p className="text-gray-300 mt-1">
                                          = ${ticket.financial_exposure.breach_penalty.toLocaleString()}
                                        </p>
                                      </div>
                                    )}

                                    {/* Total */}
                                    <div className="border-t-2 border-gray-700 pt-3 mt-3">
                                      <div className="flex justify-between items-center">
                                        <span className="text-white font-bold">Total Financial Exposure:</span>
                                        <span className="text-2xl font-bold text-red-400">
                                          ${ticket.financial_exposure.total.toLocaleString()}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                {/* ROSI Analysis */}
                                <div className="bg-gradient-to-r from-green-900/20 to-emerald-900/20 rounded-lg p-4 border border-green-800/50">
                                  <h6 className="text-sm font-bold text-green-300 uppercase mb-3">📊 Return on Security Investment (ROSI)</h6>

                                  <div className="grid grid-cols-2 gap-4 mb-3">
                                    <div>
                                      <p className="text-xs text-gray-400 uppercase">Fix Cost</p>
                                      <p className="text-lg font-bold text-blue-400">${ticket.rosi.fix_cost.toLocaleString()}</p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-gray-400 uppercase">Net Benefit</p>
                                      <p className="text-lg font-bold text-green-400">${ticket.rosi.net_benefit.toLocaleString()}</p>
                                    </div>
                                  </div>

                                  <div className="bg-black/40 rounded p-3">
                                    <div className="flex justify-between items-center mb-2">
                                      <span className="text-sm text-gray-300">ROSI Percentage:</span>
                                      <span className="text-2xl font-bold text-green-400">{ticket.rosi.rosi_percentage.toFixed(0)}%</span>
                                    </div>
                                    <p className="text-xs text-gray-400 italic">
                                      Formula: (Risk Reduction - Fix Cost) / Fix Cost × 100
                                    </p>
                                  </div>

                                  <div className="mt-3 p-2 bg-green-900/30 rounded border border-green-800">
                                    <p className="text-sm text-green-300 font-semibold">
                                      💡 {ticket.rosi.recommendation}
                                    </p>
                                  </div>
                                </div>

                                {/* Technical Details */}
                                <details className="bg-gray-800/50 rounded-lg">
                                  <summary className="px-4 py-3 cursor-pointer hover:bg-gray-800 rounded-lg transition font-semibold text-gray-300">
                                    🔧 Technical Details
                                  </summary>
                                  <div className="px-4 py-3 space-y-2 text-sm">
                                    <div className="grid grid-cols-2 gap-2">
                                      <div>
                                        <p className="text-gray-400">File:</p>
                                        <p className="text-gray-200 font-mono text-xs">{ticket.technical_details.file}</p>
                                      </div>
                                      <div>
                                        <p className="text-gray-400">Line:</p>
                                        <p className="text-gray-200">{ticket.technical_details.line}</p>
                                      </div>
                                      <div>
                                        <p className="text-gray-400">Package:</p>
                                        <p className="text-gray-200">{ticket.technical_details.package}</p>
                                      </div>
                                      <div>
                                        <p className="text-gray-400">Rule ID:</p>
                                        <p className="text-gray-200 font-mono text-xs">{ticket.technical_details.rule_id}</p>
                                      </div>
                                    </div>
                                    <div>
                                      <p className="text-gray-400 mb-1">Description:</p>
                                      <p className="text-gray-300 text-xs">{ticket.technical_details.original_message}</p>
                                    </div>
                                  </div>
                                </details>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
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
          </>
        )}

        {/* Uploads Tab */}
        {activeTab === 'uploads' && (
          <div className="space-y-6">
            <AssetInventoryUpload />
            <FinancialDocUpload />
          </div>
        )}
      </div>
    </div>
  );
}
