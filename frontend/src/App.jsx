import React, { useState, useEffect } from 'react';
import RepositoryDashboard from './components/RepositoryDashboard';
import ChatInterface from './components/ChatInterface';
import CodeViewer from './components/CodeViewer';
import {
  fetchRepositories,
  indexRepository,
  sendChatMessage,
  fetchFileContent,
} from './services/api';

export default function App() {
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [reposLoading, setReposLoading] = useState(false);

  // Citation code viewer states
  const [activeCitation, setActiveCitation] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [codeLoading, setCodeLoading] = useState(false);
  const [codeError, setCodeError] = useState('');

  // Load repositories on startup
  const loadRepos = async () => {
    try {
      setReposLoading(true);
      const data = await fetchRepositories();
      setRepositories(data);
      if (data.length > 0 && !selectedRepo) {
        setSelectedRepo(data[0]);
      }
    } catch (err) {
      console.error('Error fetching repos:', err);
    } finally {
      setReposLoading(false);
    }
  };

  useEffect(() => {
    loadRepos();
  }, []);

  // Poll repos if any is currently indexing
  useEffect(() => {
    const hasIndexing = repositories.some(
      (r) => r.status === 'indexing' || r.status === 'cloning'
    );
    if (!hasIndexing) return;

    const interval = setInterval(async () => {
      try {
        const data = await fetchRepositories();
        setRepositories(data);
        if (selectedRepo) {
          const updated = data.find((r) => r.repository_id === selectedRepo.repository_id);
          if (updated) setSelectedRepo(updated);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [repositories, selectedRepo]);

  // Handle repository selection
  const handleSelectRepo = (repo) => {
    setSelectedRepo(repo);
    setMessages([]);
    setSessionId(null);
    setActiveCitation(null);
  };

  // Handle indexing a new repository
  const handleIndexRepo = async (url) => {
    const res = await indexRepository(url);
    await loadRepos();
    if (res.repository) {
      setSelectedRepo(res.repository);
    }
  };

  // Handle sending a chat question
  const handleSendMessage = async (userText) => {
    if (!selectedRepo) return;

    const newMsg = { role: 'user', content: userText };
    setMessages((prev) => [...prev, newMsg]);
    setChatLoading(true);

    try {
      const response = await sendChatMessage(
        selectedRepo.repository_id,
        userText,
        sessionId
      );

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          citations: response.citations || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err.message}`,
          citations: [],
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Handle opening a citation
  const handleOpenCitation = async (citation) => {
    if (!selectedRepo) return;
    setActiveCitation(citation);
    setCodeLoading(true);
    setCodeError('');
    try {
      const data = await fetchFileContent(
        selectedRepo.repository_id,
        citation.file_path,
        citation.start_line,
        citation.end_line
      );
      setFileData(data);
    } catch (err) {
      setCodeError(err.message || 'Failed to read source file');
    } finally {
      setCodeLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950">
      {/* Sidebar Dashboard */}
      <RepositoryDashboard
        repositories={repositories}
        selectedRepo={selectedRepo}
        onSelectRepo={handleSelectRepo}
        onIndexRepo={handleIndexRepo}
        onRefresh={loadRepos}
        loading={reposLoading}
      />

      {/* Main Chat Area */}
      <ChatInterface
        selectedRepo={selectedRepo}
        messages={messages}
        onSendMessage={handleSendMessage}
        onOpenCitation={handleOpenCitation}
        loading={chatLoading}
      />

      {/* Sliding Source Code Viewer */}
      <CodeViewer
        citation={activeCitation}
        fileData={fileData}
        loading={codeLoading}
        error={codeError}
        onClose={() => setActiveCitation(null)}
      />
    </div>
  );
}
