import React, { useState, useRef } from 'react';
import { UploadCloud, Film, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { VideoMetadata } from '../types';

interface EmptyUploadProps {
  onUploadSuccess: (video: VideoMetadata) => void;
  onCancel?: () => void;
}

export const EmptyUpload: React.FC<EmptyUploadProps> = ({ onUploadSuccess, onCancel }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      setErrorMessage(`Unsupported format. Please upload MP4, AVI, MOV, or WEBM.`);
      return;
    }

    setErrorMessage(null);
    setIsUploading(true);

    try {
      const uploadedVideo = await api.uploadVideo(file);
      setIsUploading(false);
      onUploadSuccess(uploadedVideo);
    } catch (err: any) {
      setIsUploading(false);
      setErrorMessage(err.message || 'Video upload failed. Please try again.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="max-w-2xl mx-auto p-8 bg-white border border-slate-200 rounded-xl shadow-sm text-center">
      <div className="w-12 h-12 mx-auto rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-4">
        <Film className="w-6 h-6" />
      </div>

      <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
        <span className="font-semibold text-slate-700">TimeSense AI</span>: Not just what happened &mdash; what happened, when, in what order, and for how long.
      </p>

      {/* Drag & Drop Target */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`mt-6 border-2 border-dashed rounded-lg p-10 cursor-pointer transition-colors ${
          isDragging
            ? 'border-indigo-500 bg-indigo-50/50'
            : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 hover:bg-slate-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            <div className="text-sm font-medium text-slate-700">Uploading and inspecting video metadata...</div>
            <div className="text-xs text-slate-400">Extracting FPS, frame count, resolution via OpenCV</div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <UploadCloud className="w-8 h-8 text-slate-400" />
            <div>
              <span className="text-sm font-semibold text-indigo-600 hover:text-indigo-700">Choose a video file</span>
              <span className="text-sm text-slate-500"> or drag and drop here</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              {['MP4', 'AVI', 'MOV', 'WEBM'].map((fmt) => (
                <span
                  key={fmt}
                  className="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide bg-slate-200/60 text-slate-600 border border-slate-300/60"
                >
                  {fmt}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center gap-2 text-xs text-rose-700 text-left">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {onCancel && (
        <div className="mt-6 flex justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};
