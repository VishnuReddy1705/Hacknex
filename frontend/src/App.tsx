import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { EmptyUpload } from './components/EmptyUpload';
import { OverviewPage } from './pages/OverviewPage';
import { VideoAnalysisPage } from './pages/VideoAnalysisPage';
import { EventTimelinePage } from './pages/EventTimelinePage';
import { AskVideoPage } from './pages/AskVideoPage';
import { EntitiesPage } from './pages/EntitiesPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './services/api';
import { VideoMetadata, TemporalEvent, EntityTrack } from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [videos, setVideos] = useState<VideoMetadata[]>([]);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const [activeVideo, setActiveVideo] = useState<VideoMetadata | null>(null);
  const [events, setEvents] = useState<TemporalEvent[]>([]);
  const [entities, setEntities] = useState<EntityTrack[]>([]);
  const [seekTime, setSeekTime] = useState<number | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [systemHealth, setSystemHealth] = useState<any>(null);

  // Fetch system health
  useEffect(() => {
    api.getHealth()
      .then(setSystemHealth)
      .catch((err) => console.warn('Backend offline or health check failed', err));
  }, []);

  // Fetch video list on startup
  const loadVideos = useCallback(async () => {
    try {
      const list = await api.listVideos();
      setVideos(list);
      if (list.length > 0 && !activeVideoId) {
        setActiveVideoId(list[0].id);
        setActiveVideo(list[0]);
      } else if (activeVideoId) {
        const found = list.find((v) => v.id === activeVideoId);
        if (found) setActiveVideo(found);
      }
    } catch (err) {
      console.warn('Could not fetch video list', err);
    }
  }, [activeVideoId]);

  useEffect(() => {
    loadVideos();
  }, [loadVideos]);

  // Load events and entities whenever active video changes
  const loadVideoData = useCallback(async (videoId: string) => {
    try {
      const [evs, ents] = await Promise.all([
        api.getEvents(videoId),
        api.getEntities(videoId),
      ]);
      setEvents(evs);
      setEntities(ents);
    } catch (err) {
      console.warn('Error loading video events/entities', err);
    }
  }, []);

  useEffect(() => {
    if (activeVideoId) {
      loadVideoData(activeVideoId);
    } else {
      setEvents([]);
      setEntities([]);
    }
  }, [activeVideoId, loadVideoData]);

  // Polling for processing status when video is actively processing
  useEffect(() => {
    if (!activeVideo || activeVideo.status === 'idle' || activeVideo.status === 'ready' || activeVideo.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const status = await api.getVideoStatus(activeVideo.id);
        setActiveVideo((prev) => prev ? {
          ...prev,
          status: status.status,
          progress_pct: status.progress_pct,
          current_stage_label: status.current_stage_label,
          error_message: status.error_message
        } : null);

        if (status.status === 'ready') {
          // Finished! Reload all
          loadVideos();
          loadVideoData(activeVideo.id);
        }
      } catch (err) {
        console.error('Error polling video status', err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [activeVideo?.status, activeVideo?.id, loadVideos, loadVideoData]);

  const handleSelectVideo = (videoId: string) => {
    setActiveVideoId(videoId);
    const found = videos.find((v) => v.id === videoId);
    if (found) setActiveVideo(found);
  };

  const handleUploadSuccess = (video: VideoMetadata) => {
    setVideos((prev) => [video, ...prev]);
    setActiveVideoId(video.id);
    setActiveVideo(video);
    setIsUploadModalOpen(false);
    setCurrentTab('overview');
  };

  const handleSeek = (seconds: number) => {
    setSeekTime(seconds);
  };

  return (
    <div className="flex h-screen bg-[#f8fafc] text-slate-800 antialiased overflow-hidden font-sans">
      {/* Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        systemHealth={systemHealth}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navigation & Status Bar */}
        <TopBar
          videos={videos}
          activeVideo={activeVideo}
          onSelectVideo={handleSelectVideo}
          onOpenUpload={() => setIsUploadModalOpen(true)}
        />

        {/* Dynamic Page Views */}
        <main className="flex-1 overflow-y-auto">
          {currentTab === 'overview' && (
            <OverviewPage
              activeVideo={activeVideo}
              events={events}
              entities={entities}
              onNavigateToAnalysis={() => setCurrentTab('analysis')}
              onNavigateToAsk={() => setCurrentTab('ask')}
              onSeekToTime={handleSeek}
              onRefreshData={() => {
                loadVideos();
                if (activeVideoId) loadVideoData(activeVideoId);
              }}
            />
          )}

          {currentTab === 'analysis' && (
            <VideoAnalysisPage
              activeVideo={activeVideo}
              events={events}
              entities={entities}
              seekTime={seekTime}
              onSeek={handleSeek}
              onRefreshData={() => {
                loadVideos();
                if (activeVideoId) loadVideoData(activeVideoId);
              }}
            />
          )}

          {currentTab === 'timeline' && (
            <EventTimelinePage
              activeVideo={activeVideo}
              events={events}
              onSeekToTime={handleSeek}
              onNavigateToAnalysis={() => setCurrentTab('analysis')}
            />
          )}

          {currentTab === 'ask' && (
            <AskVideoPage
              activeVideo={activeVideo}
              onSeekToTime={handleSeek}
              onNavigateToAnalysis={() => setCurrentTab('analysis')}
            />
          )}

          {currentTab === 'entities' && (
            <EntitiesPage
              activeVideo={activeVideo}
              entities={entities}
              events={events}
              onSeekToTime={handleSeek}
              onNavigateToAnalysis={() => setCurrentTab('analysis')}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsPage systemHealth={systemHealth} />
          )}
        </main>
      </div>

      {/* Upload Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden">
            <EmptyUpload
              onUploadSuccess={handleUploadSuccess}
              onCancel={() => setIsUploadModalOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
