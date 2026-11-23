import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Code2, Sparkles, Terminal } from 'lucide-react';

export default function ChatInterface({
  selectedRepo,
  messages,
  onSendMessage,
  onOpenCitation,
  loading,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !selectedRepo) return;
    const msg = input.trim();
    setInput('');
    onSendMessage(msg);
  };

  if (!selectedRepo) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500">
        <Bot className="w-12 h-12 text-slate-600 mb-3 stroke-[1.5]" />
        <h2 className="text-base font-semibold text-slate-300 mb-1">
          No Repository Selected
        </h2>
        <p className="text-xs max-w-sm text-slate-500">
          Choose a repository from the left panel or enter a new GitHub URL to index.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950">
      {/* Top Bar */}
      <div className="px-6 py-3.5 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40 backdrop-blur">
        <div>
          <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            {selectedRepo.repository_name}
          </h2>
          <p className="text-[11px] text-slate-400">
            {selectedRepo.total_files} files • {selectedRepo.total_chunks} chunks indexed
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-indigo-400 bg-indigo-950/40 border border-indigo-800/40 px-2.5 py-1 rounded-full">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Hybrid RAG + Citations</span>
        </div>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center py-12 max-w-md mx-auto">
            <div className="w-10 h-10 rounded-full bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center mx-auto mb-3 text-indigo-400">
              <Terminal className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">
              Ask about {selectedRepo.repository_name}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              RepoSage uses hybrid semantic retrieval, BM25 keyword matching, and cross-encoder reranking to answer questions with verified code citations.
            </p>
            <div className="grid grid-cols-1 gap-2 text-left">
              {[
                "Where is the main entry point or router configured?",
                "How does the authentication and session flow work?",
                "Which files handle database queries and storage?",
              ].map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(suggestion)}
                  className="p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 transition-colors cursor-pointer text-left"
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-xs'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-xs'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Citations section */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-800/80">
                  <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-indigo-400" />
                    Source Citations ({msg.citations.length})
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {msg.citations.map((c, cIdx) => (
                      <button
                        key={cIdx}
                        onClick={() => onOpenCitation(c)}
                        className="px-2.5 py-1 rounded bg-slate-950/80 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-600/60 text-[11px] font-mono text-indigo-300 transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
                      >
                        <span className="truncate max-w-[200px]">{c.file_path}</span>
                        <span className="text-slate-500">L{c.start_line}-{c.end_line}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-slate-800 text-slate-300 flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3.5 items-start">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl rounded-tl-xs text-xs text-slate-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></div>
              <span>Searching code and formulating response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/30">
        <form onSubmit={handleSubmit} className="flex gap-2 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder={
              selectedRepo.status === 'ready'
                ? `Ask anything about ${selectedRepo.repository_name}...`
                : `Repository is ${selectedRepo.status}...`
            }
            className="flex-1 text-xs px-4 py-3 bg-slate-900/80 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 text-slate-100 placeholder-slate-500 disabled:opacity-50 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !input.trim() || selectedRepo.status !== 'ready'}
            className="px-4 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl flex items-center justify-center transition-colors cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
