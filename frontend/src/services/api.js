const API_BASE = '/api';

export async function fetchRepositories() {
  const res = await fetch(`${API_BASE}/repositories`);
  if (!res.ok) throw new Error('Failed to load repositories');
  return res.json();
}

export async function indexRepository(repository_url) {
  const res = await fetch(`${API_BASE}/repositories/index`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Indexing failed' }));
    throw new Error(err.detail || 'Failed to trigger indexing');
  }
  return res.json();
}

export async function fetchRepositoryDetails(repository_id) {
  const res = await fetch(`${API_BASE}/repositories/${repository_id}`);
  if (!res.ok) throw new Error('Failed to load repository details');
  return res.json();
}

export async function fetchFileContent(repository_id, filePath, startLine, endLine) {
  const params = new URLSearchParams({ path: filePath });
  if (startLine) params.append('start_line', startLine);
  if (endLine) params.append('end_line', endLine);

  const res = await fetch(`${API_BASE}/repositories/${repository_id}/file?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch file' }));
    throw new Error(err.detail || 'File not found');
  }
  return res.json();
}

export async function sendChatMessage(repository_id, message, session_id = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_id,
      message,
      session_id,
      use_reranker: true,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Chat request failed' }));
    throw new Error(err.detail || 'Failed to get answer');
  }
  return res.json();
}
