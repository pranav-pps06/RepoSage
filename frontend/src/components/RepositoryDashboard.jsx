import React, { useState } from 'react';
import { GitBranch, Database, Layers, RefreshCw, AlertCircle, CheckCircle2, ChevronRight, Plus } from 'lucide-react';

export default function RepositoryDashboard({
  repositories,
  selectedRepo,
  onSelectRepo,
  onIndexRepo,
  onRefresh,
  loading,
}) {
  const [repoUrl, setRepoUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setError('');
    setSubmitting(true);
    try {
      await onIndexRepo(repoUrl.trim());
      setRepoUrl('');
    } catch (err) {
      setError(err.message || 'Failed to index repository');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-80 shrink-0 border-r border-slate-800/80 bg-slate-900/60 flex flex-col h-full">
      {/* Top Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold text-base border border-indigo-500/30">
            RS
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-wide text-slate-100">RepoSage</h1>
            <p className="text-[11px] text-slate-400">Codebase Intelligence</p>
          </div>
        </div>
        <button
          onClick={onRefresh}
          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
          title="Refresh Repositories"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
        </button>
      </div>

      {/* Index Repo Input */}
      <form onSubmit={handleSubmit} className="p-4 border-b border-slate-800/80 space-y-2">
        <label className="text-xs font-medium text-slate-300 block">
          Add Public Repository
        </label>
        <div className="space-y-2">
          <input
            type="url"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/org/repo"
            required
            className="w-full text-xs px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-lg focus:outline-none focus:border-indigo-500 text-slate-200 placeholder-slate-600 transition-colors"
          />
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2 px-3 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg flex items-center justify-center gap-1.5 transition-colors shadow-sm cursor-pointer"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Indexing...
              </>
            ) : (
              <>
                <Plus className="w-3.5 h-3.5" />
                Index Repository
              </>
            )}
          </button>
        </div>
        {error && (
          <p className="text-[11px] text-red-400 flex items-center gap-1 pt-1">
            <AlertCircle className="w-3 h-3 shrink-0" />
            {error}
          </p>
        )}
      </form>

      {/* Repositories List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-2">
          Indexed Repositories ({repositories.length})
        </div>

        {repositories.length === 0 && !loading && (
          <div className="p-4 text-center text-xs text-slate-500">
            No repositories indexed yet. Enter a GitHub URL above to get started.
          </div>
        )}

        {repositories.map((repo) => {
          const isSelected = selectedRepo?.repository_id === repo.repository_id;
          const isReady = repo.status === 'ready';

          return (
            <div
              key={repo.repository_id}
              onClick={() => onSelectRepo(repo)}
              className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                isSelected
                  ? 'bg-indigo-950/40 border-indigo-500/50 text-white shadow-sm'
                  : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-semibold truncate max-w-[170px] text-slate-100">
                  {repo.repository_name}
                </span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-full uppercase font-mono ${
                    isReady
                      ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                      : repo.status === 'failed'
                      ? 'bg-red-950/60 text-red-400 border border-red-800/40'
                      : 'bg-amber-950/60 text-amber-400 border border-amber-800/40 animate-pulse'
                  }`}
                >
                  {repo.status}
                </span>
              </div>

              {/* Repo Stats */}
              <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-400 mb-2">
                <span className="flex items-center gap-1">
                  <Database className="w-3 h-3 text-slate-500" />
                  {repo.total_files} files
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="w-3 h-3 text-slate-500" />
                  {repo.total_chunks} chunks
                </span>
              </div>

              {/* Languages tags */}
              {repo.languages && repo.languages.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {repo.languages.slice(0, 3).map((lang) => (
                    <span
                      key={lang}
                      className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded"
                    >
                      {lang}
                    </span>
                  ))}
                  {repo.languages.length > 3 && (
                    <span className="text-[10px] text-slate-500 self-center">
                      +{repo.languages.length - 3}
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Selected Repo Footer Banner */}
      {selectedRepo && (
        <div className="p-3 bg-slate-950 border-t border-slate-800/80 text-[11px] text-slate-400">
          <div className="truncate font-mono text-slate-300">
            Active: <span className="text-indigo-400">{selectedRepo.repository_name}</span>
          </div>
        </div>
      )}
    </div>
  );
}
