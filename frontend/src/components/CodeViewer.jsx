import React, { useEffect, useRef } from 'react';
import { X, FileCode, CheckCircle2 } from 'lucide-react';

export default function CodeViewer({ citation, fileData, loading, error, onClose }) {
  const codeContainerRef = useRef(null);

  useEffect(() => {
    if (fileData && citation?.start_line && codeContainerRef.current) {
      const lineElement = codeContainerRef.current.querySelector(
        `[data-line="${citation.start_line}"]`
      );
      if (lineElement) {
        lineElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [fileData, citation]);

  if (!citation) return null;

  const lines = fileData?.content ? fileData.content.split('\n') : [];

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 backdrop-blur">
        <div className="flex items-center gap-2 overflow-hidden">
          <FileCode className="w-5 h-5 text-indigo-400 shrink-0" />
          <div className="truncate">
            <h3 className="text-sm font-semibold text-slate-100 truncate">
              {citation.file_path}
            </h3>
            <p className="text-xs text-slate-400">
              Lines {citation.start_line} – {citation.end_line}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          title="Close viewer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Code body */}
      <div
        ref={codeContainerRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-xs bg-slate-950"
      >
        {loading && (
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mr-3"></div>
            Loading source code...
          </div>
        )}

        {error && (
          <div className="p-4 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300">
            {error}
          </div>
        )}

        {!loading && !error && lines.map((line, idx) => {
          const lineNum = idx + 1;
          const isHighlighted =
            lineNum >= citation.start_line && lineNum <= citation.end_line;

          return (
            <div
              key={lineNum}
              data-line={lineNum}
              className={`flex items-start leading-5 py-0.5 px-2 rounded ${
                isHighlighted
                  ? 'bg-indigo-950/60 border-l-2 border-indigo-400 text-slate-100'
                  : 'text-slate-400 hover:bg-slate-900/50'
              }`}
            >
              <span className="w-10 shrink-0 text-right pr-4 select-none text-slate-600 font-mono">
                {lineNum}
              </span>
              <pre className="overflow-x-auto whitespace-pre font-mono flex-1">
                {line || ' '}
              </pre>
            </div>
          );
        })}
      </div>
    </div>
  );
}
