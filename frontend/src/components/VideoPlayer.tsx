import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX, Maximize2, Sparkles } from 'lucide-react';
import { formatTimestamp } from '../utils/format';
import { api } from '../services/api';

interface VideoPlayerProps {
  videoId: string;
  hasAnnotated: boolean;
  onTimeUpdate?: (currentTime: number) => void;
  seekTime?: number | null;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoId,
  hasAnnotated,
  onTimeUpdate,
  seekTime,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showAnnotated, setShowAnnotated] = useState(hasAnnotated);

  useEffect(() => {
    setShowAnnotated(hasAnnotated);
  }, [hasAnnotated]);

  // Handle external seek triggers (e.g. clicking evidence timestamps)
  useEffect(() => {
    if (seekTime !== null && seekTime !== undefined && videoRef.current) {
      videoRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
      if (videoRef.current.paused) {
        videoRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    }
  }, [seekTime]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const time = videoRef.current.currentTime;
    setCurrentTime(time);
    if (onTimeUpdate) onTimeUpdate(time);
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    setDuration(videoRef.current.duration || 0);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  const handleFullscreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen();
      }
    }
  };

  const videoSrc = api.getVideoStreamUrl(videoId, showAnnotated);

  return (
    <div className="flex flex-col bg-slate-900 rounded-lg overflow-hidden border border-slate-300 shadow-sm">
      {/* Video Container */}
      <div className="relative aspect-video bg-black flex items-center justify-center group">
        <video
          ref={videoRef}
          key={`${videoId}-${showAnnotated}`}
          src={videoSrc}
          className="w-full h-full object-contain"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          muted={isMuted}
          playsInline
        />

        {/* Annotated Stream Indicator Badge */}
        {hasAnnotated && (
          <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-black/75 backdrop-blur-sm text-white border border-white/20">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{showAnnotated ? 'Track Overlay: ON' : 'Raw Video: ON'}</span>
          </div>
        )}

        {/* Center Play Overlay on pause */}
        {!isPlaying && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-white/90 text-slate-900 flex items-center justify-center hover:scale-105 transition-transform shadow-lg cursor-pointer"
          >
            <Play className="w-6 h-6 ml-1 fill-slate-900" />
          </button>
        )}
      </div>

      {/* Control Bar */}
      <div className="bg-slate-950 px-4 py-2.5 flex flex-col gap-2 border-t border-slate-800 text-white">
        {/* Progress Scrubber */}
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={duration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-400"
          />
        </div>

        {/* Bottom Actions */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-200 hover:text-white transition-colors"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
            </button>

            <button
              onClick={() => {
                if (videoRef.current) {
                  videoRef.current.currentTime = 0;
                  setCurrentTime(0);
                }
              }}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Restart"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            {/* Time readout */}
            <div className="font-mono text-xs text-slate-300">
              <span className="text-white font-medium">{formatTimestamp(currentTime)}</span>
              <span className="text-slate-500 mx-1">/</span>
              <span>{formatTimestamp(duration)}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Toggle Annotated Overlay */}
            {hasAnnotated && (
              <button
                onClick={() => setShowAnnotated(!showAnnotated)}
                className={`px-2 py-1 rounded text-xs font-medium border transition-colors ${
                  showAnnotated
                    ? 'bg-indigo-600/30 text-indigo-300 border-indigo-500/50'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                }`}
              >
                Track IDs
              </button>
            )}

            {/* Playback speed selector */}
            <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded px-1 py-0.5">
              {[1, 1.5, 2].map((s) => (
                <button
                  key={s}
                  onClick={() => handleSpeedChange(s)}
                  className={`px-1.5 py-0.5 rounded text-[11px] font-medium transition-colors ${
                    playbackSpeed === s ? 'bg-slate-800 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>

            {/* Audio toggle */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>

            {/* Fullscreen */}
            <button
              onClick={handleFullscreen}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
