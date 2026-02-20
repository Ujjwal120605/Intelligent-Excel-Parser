"use client";

import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, Layers, X } from "lucide-react";
import axios from "axios";

// TypeScript interfaces for API response
interface ParsedData {
  row: number;
  col: number;
  param_name: string;
  asset_name: string | null;
  raw_value: any;
  parsed_value: number | null;
  confidence: string;
}

interface UnmappedColumn {
  col: number;
  header: string;
  reason: string;
}

interface APIResponse {
  status: string;
  header_row: number;
  parsed_data: ParsedData[];
  unmapped_columns: UnmappedColumn[];
  warnings: string[];
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiResponse, setApiResponse] = useState<APIResponse | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setApiResponse(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxFiles: 1,
  });

  const analyzeFile = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Use environment variable for backend URL, fallback to localhost for development
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const res = await axios.post(`${backendUrl}/parse`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setApiResponse(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to parse file.");
    } finally {
      setLoading(false);
    }
  };

  const downloadJson = () => {
    if (!apiResponse) return;
    const jsonString = JSON.stringify(apiResponse, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "latspace_parsed_data.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const reset = () => {
    setFile(null);
    setApiResponse(null);
    setError(null);
    setLoading(false);
  }

  return (
    <div className="flex flex-col h-full flex-grow text-black">
      {/* Header */}
      <header className="flex justify-between items-center p-6 brutal-border-b bg-white">
        <h1 className="text-3xl font-extrabold tracking-tighter uppercase cursor-pointer" onClick={reset}>LATSPACE AI</h1>
        <div className="flex items-center gap-2 text-xs font-bold tracking-widest uppercase">
          <span className={`w-2 h-2 rounded-full ${loading ? 'bg-yellow-500 animate-pulse' : 'bg-[#22c55e]'}`}></span>
          {loading ? "ANALYZING..." : "SYSTEM READY"}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-grow flex flex-col p-6 bg-[#fafafa] overflow-hidden">
        {!apiResponse && !loading && (
          <div {...getRootProps()} className={`flex flex-col items-center justify-center flex-grow border-2 border-dashed ${isDragActive ? 'border-black bg-gray-100' : 'border-gray-300'} p-12 cursor-pointer transition-colors duration-200 min-h-[400px]`}>
            <input {...getInputProps()} />
            <Layers size={64} strokeWidth={1} className="text-gray-400 mb-6" />
            <p className="text-gray-500 font-mono text-xs tracking-widest uppercase">
              {file ? `SELECTED: ${file.name}` : "DRAG & DROP EXCEL FILE TO BEGIN"}
            </p>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center flex-grow p-12 min-h-[400px]">
            <div className="animate-spin w-12 h-12 border-4 border-black border-t-transparent border-r-transparent mb-6"></div>
            <p className="font-mono text-xs tracking-widest uppercase">PROCESSING DATA MATRIX...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 brutal-border p-4 mb-4 text-red-600 font-mono text-sm">
            ERROR: {error}
          </div>
        )}

        {apiResponse && (
          <div className="flex flex-col flex-grow overflow-auto h-[400px]">
            {apiResponse.warnings && apiResponse.warnings.length > 0 && (
              <div className="bg-yellow-50 brutal-border p-4 mb-4 flex-shrink-0">
                <h3 className="font-bold flex items-center gap-2 mb-2 text-sm uppercase">WARNINGS</h3>
                <ul className="list-disc pl-5 font-mono text-xs">
                  {apiResponse.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            {apiResponse.unmapped_columns && apiResponse.unmapped_columns.length > 0 && (
              <div className="bg-red-50 brutal-border p-4 mb-4 flex-shrink-0">
                <h3 className="font-bold flex items-center gap-2 mb-2 text-sm uppercase text-red-800">UNMAPPED COLUMNS</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs font-mono">
                    <thead className="bg-red-100 text-red-900 uppercase text-[10px] tracking-wider">
                      <tr>
                        <th className="p-2 border border-red-300">COL</th>
                        <th className="p-2 border border-red-300">HEADER</th>
                        <th className="p-2 border border-red-300">REASON</th>
                      </tr>
                    </thead>
                    <tbody>
                      {apiResponse.unmapped_columns.map((col, i) => (
                        <tr key={i} className="border-b border-red-200">
                          <td className="p-2 border border-red-200">{col.col}</td>
                          <td className="p-2 border border-red-200 font-bold">{col.header}</td>
                          <td className="p-2 border border-red-200 text-gray-600">{col.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="flex-grow overflow-auto brutal-border bg-white">
              <table className="w-full text-left border-collapse text-sm">
                <thead className="bg-black text-white font-mono uppercase text-[10px] tracking-wider sticky top-0 z-10">
                  <tr>
                    <th className="p-3">ROW</th>
                    <th className="p-3">COL</th>
                    <th className="p-3">PARAMETER</th>
                    <th className="p-3">ASSET</th>
                    <th className="p-3">RAW VAL</th>
                    <th className="p-3 text-right">PARSED</th>
                    <th className="p-3 text-center">CONF</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-xs">
                  {apiResponse.parsed_data.map((row, i) => (
                    <tr key={i} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                      <td className="p-3">{row.row}</td>
                      <td className="p-3">{row.col}</td>
                      <td className="p-3 font-bold">{row.param_name}</td>
                      <td className="p-3 text-gray-600">{row.asset_name || "-"}</td>
                      <td className="p-3 text-gray-500 truncate max-w-[150px]">{row.raw_value}</td>
                      <td className="p-3 text-right bg-gray-50 font-bold">{row.parsed_value !== null ? row.parsed_value : "-"}</td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-1 text-[9px] uppercase font-bold tracking-widest ${row.confidence === 'high' ? 'bg-green-100 text-green-800' : row.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                          {row.confidence}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {apiResponse.parsed_data.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-gray-500 uppercase tracking-widest">
                        No parameters mapped.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Command Bar */}
      <div className="brutal-border-t p-4 flex flex-col md:flex-row items-center bg-white gap-4">
        <div className="flex-grow w-full flex items-center border-2 border-black">
          <div className="p-3 border-r-2 border-black bg-gray-50 text-gray-600">
            <UploadCloud size={20} />
          </div>
          <div className="flex-grow font-mono text-xs font-bold tracking-widest p-3 truncate text-gray-700 bg-white uppercase">
            {file ? `TARGET: ${file.name}` : "AWAITING EXCEL INPUT..."}
          </div>
          {file && (
            <button
              onClick={reset}
              className="p-3 border-l-2 border-black bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
              title="Cancel and reset"
            >
              <X size={20} />
            </button>
          )}
        </div>

        <div className="flex gap-2">
          {!apiResponse ? (
            <button
              onClick={analyzeFile}
              disabled={!file || loading}
              className="w-full md:w-auto px-8 py-3 bg-black text-white font-bold uppercase tracking-widest disabled:opacity-50 brutal-shadow-hover active:brutal-shadow-active hover:bg-gray-800 transition-colors whitespace-nowrap"
            >
              ANALYZE DATA
            </button>
          ) : (
            <>
              <button
                onClick={reset}
                className="w-full md:w-auto px-6 py-3 bg-gray-200 border-2 border-black font-bold uppercase tracking-widest brutal-shadow-hover active:brutal-shadow-active hover:bg-gray-300 transition-all whitespace-nowrap text-black"
              >
                RESET
              </button>
              <button
                onClick={downloadJson}
                className="w-full md:w-auto px-8 py-3 bg-[#22c55e] border-2 border-black font-bold uppercase tracking-widest brutal-shadow-hover active:brutal-shadow-active hover:bg-green-400 transition-all whitespace-nowrap text-black"
              >
                DOWNLOAD JSON
              </button>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="brutal-border-t py-2 text-center text-[10px] font-bold tracking-[0.2em] font-mono bg-white">
        V2.0.0 // LATSPACE DATA PARSER
      </footer>
    </div>
  );
}
