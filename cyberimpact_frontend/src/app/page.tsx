"use client";
import React, { useState } from "react";
import axios from "axios";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [tools, setTools] = useState({
    nikto: true, clamav: true, openvas: false, trivy: true, semgrep: true,
  });

  const submit = async () => {
    setRunning(true);
    setResult(null);
    try {
      if (repoUrl) {
        const resp = await axios.post("http://localhost:8000/scan/clone", {
          repo_url: repoUrl
        });
        setResult(resp.data);
      } else {
        // Fallback for existing logic or file upload if needed later
        const form = new FormData();
        if (file) form.append("repo_zip", file);
        form.append("tools", JSON.stringify(tools));

        const resp = await axios.post("/api/scan", form, {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 600000
        });
        setResult(resp.data);
      }
    } catch (err: any) {
      console.error(err);
      setResult({ error: err?.response?.data?.detail || err.message });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 flex flex-col items-center p-8">
      <div className="w-full max-w-2xl">

        {/* Header */}
        <h1 className="text-4xl font-extrabold mb-4 text-white tracking-tight">
          🔍 Repository Security Scanner
        </h1>
        <p className="text-gray-400 mb-8">
          Scan GitHub repositories or uploaded ZIP files with multiple security analyzers.
        </p>

        {/* Card */}
        <div className="bg-gray-900/60 backdrop-blur-md shadow-xl rounded-xl border border-gray-800 p-6 space-y-6">

          {/* GitHub URL */}
          <div>
            <label className="block text-sm mb-2 font-semibold text-gray-300">
              GitHub Repository URL
            </label>
            <input
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              className="w-full rounded-lg bg-gray-800 text-gray-100 px-4 py-2 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm mb-2 font-semibold text-gray-300">
              Or Upload Repository ZIP File
            </label>
            <input
              type="file"
              accept=".zip"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg 
                         file:border-0 file:bg-blue-600 file:text-white file:cursor-pointer 
                         bg-gray-800 rounded-lg p-2 border border-gray-700 cursor-pointer"
            />
          </div>

          {/* Tools */}
          <div>
            <label className="block text-sm mb-3 font-semibold text-gray-300">Select Tools</label>
            <div className="flex flex-wrap gap-4">
              {Object.keys(tools).map((tool) => (
                <label
                  key={tool}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-800 rounded-lg border border-gray-700 cursor-pointer hover:bg-gray-700"
                >
                  <input
                    type="checkbox"
                    checked={(tools as any)[tool]}
                    onChange={(e) =>
                      setTools((prev) => ({ ...prev, [tool]: e.target.checked }))
                    }
                    className="accent-blue-500"
                  />
                  <span className="capitalize">{tool}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Button */}
          <button
            onClick={submit}
            disabled={running}
            className={`w-full py-3 rounded-lg text-lg font-semibold transition 
              ${running
                ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 text-white"}
            `}
          >
            {running ? "Running Scan..." : "Run Security Scan"}
          </button>
        </div>

        {/* Results */}
        <div className="mt-10">
          <h3 className="text-2xl font-bold mb-3">Scan Results</h3>
          <pre className="bg-gray-900 p-6 rounded-xl border border-gray-800 text-gray-300 overflow-auto whitespace-pre-wrap">
            {result ? JSON.stringify(result, null, 2) : "No results yet."}
          </pre>
        </div>
      </div>
    </div>
  );
}
