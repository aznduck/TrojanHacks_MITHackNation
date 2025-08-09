"use client";

import React, { useState, useEffect, useCallback } from "react";
import { AgentEvent } from "@/lib/types";

interface ReplayControlsProps {
  events: AgentEvent[];
  currentEventIndex: number;
  onEventIndexChange: (index: number) => void;
  onPlayStateChange?: (isPlaying: boolean) => void;
  className?: string;
}

export default function ReplayControls({
  events,
  currentEventIndex,
  onEventIndexChange,
  onPlayStateChange,
  className = "",
}: ReplayControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [intervalId, setIntervalId] = useState<NodeJS.Timeout | null>(null);

  // Calculate progress
  const progress =
    events.length > 0 ? (currentEventIndex / (events.length - 1)) * 100 : 0;
  const currentEvent = events[currentEventIndex];

  // Play/Pause functionality
  const togglePlayback = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  // Notify parent of play state changes
  useEffect(() => {
    onPlayStateChange?.(isPlaying);
  }, [isPlaying, onPlayStateChange]);

  // Step controls
  const stepForward = useCallback(() => {
    if (currentEventIndex < events.length - 1) {
      onEventIndexChange(currentEventIndex + 1);
    }
  }, [currentEventIndex, events.length, onEventIndexChange]);

  const stepBackward = useCallback(() => {
    if (currentEventIndex > 0) {
      onEventIndexChange(currentEventIndex - 1);
    }
  }, [currentEventIndex, onEventIndexChange]);

  const goToStart = useCallback(() => {
    onEventIndexChange(0);
    setIsPlaying(false);
    onPlayStateChange?.(false);
  }, [onEventIndexChange, onPlayStateChange]);

  const goToEnd = useCallback(() => {
    onEventIndexChange(events.length - 1);
    setIsPlaying(false);
    onPlayStateChange?.(false);
  }, [events.length, onEventIndexChange, onPlayStateChange]);

  // Speed control
  const changeSpeed = useCallback((speed: number) => {
    setPlaybackSpeed(speed);
  }, []);

  // Timeline scrubbing
  const handleTimelineClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const percentage = clickX / rect.width;
      const targetIndex = Math.round(percentage * (events.length - 1));
      onEventIndexChange(Math.max(0, Math.min(targetIndex, events.length - 1)));
    },
    [events.length, onEventIndexChange]
  );

  // Auto-play effect
  useEffect(() => {
    if (isPlaying && currentEventIndex < events.length - 1) {
      const timeout = setTimeout(() => {
        onEventIndexChange(currentEventIndex + 1);
      }, 1000 / playbackSpeed);
      setIntervalId(timeout);
      return () => clearTimeout(timeout);
    } else if (isPlaying && currentEventIndex >= events.length - 1) {
      // Auto-stop at end
      setIsPlaying(false);
      onPlayStateChange?.(false);
    }
  }, [
    isPlaying,
    currentEventIndex,
    events.length,
    playbackSpeed,
    onEventIndexChange,
    onPlayStateChange,
  ]);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalId) clearTimeout(intervalId);
    };
  }, [intervalId]);

  // Format time display
  const formatTime = (event: AgentEvent) => {
    return new Date(event.ts * 1000).toLocaleTimeString();
  };

  const formatDuration = () => {
    if (events.length === 0) return "0:00";
    const firstEvent = events[0];
    const lastEvent = events[events.length - 1];
    const duration = lastEvent.ts - firstEvent.ts;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  if (events.length === 0) {
    return null;
  }

  return (
    <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
      {/* Main Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          {/* Go to Start */}
          <button
            onClick={goToStart}
            disabled={currentEventIndex === 0}
            className="p-2 rounded-md border border-gray-800 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-gray-800"
            title="Go to start"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8.445 14.832A1 1 0 0010 14v-2.798l5.445 3.63A1 1 0 0017 14V6a1 1 0 00-1.555-.832L10 8.798V6a1 1 0 00-1.555-.832l-6 4a1 1 0 000 1.664l6 4z" />
            </svg>
          </button>

          {/* Step Backward */}
          <button
            onClick={stepBackward}
            disabled={currentEventIndex === 0}
            className="p-2 rounded-md border border-gray-800 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-gray-800"
            title="Previous event"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" />
            </svg>
          </button>

          {/* Play/Pause */}
          <button
            onClick={togglePlayback}
            className="p-3 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 4a1 1 0 011 1v10a1 1 0 01-2 0V5a1 1 0 011-1zM14 4a1 1 0 011 1v10a1 1 0 01-2 0V5a1 1 0 011-1z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8 5v10l8-5-8-5z" />
              </svg>
            )}
          </button>

          {/* Step Forward */}
          <button
            onClick={stepForward}
            disabled={currentEventIndex >= events.length - 1}
            className="p-2 rounded-md border border-gray-800 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-gray-800"
            title="Next event"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" />
            </svg>
          </button>

          {/* Go to End */}
          <button
            onClick={goToEnd}
            disabled={currentEventIndex >= events.length - 1}
            className="p-2 rounded-md border border-gray-800 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-gray-800"
            title="Go to end"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4.555 5.168A1 1 0 003 6v8a1 1 0 001.555.832L10 11.202V14a1 1 0 001.555.832l6-4a1 1 0 000-1.664l-6-4A1 1 0 0010 6v2.798l-5.445-3.63z" />
            </svg>
          </button>
        </div>

        {/* Speed Controls */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Speed:</span>
          {[0.5, 1, 2, 4].map((speed) => (
            <button
              key={speed}
              onClick={() => changeSpeed(speed)}
              className={`px-2 py-1 text-xs rounded border ${
                playbackSpeed === speed
                  ? "bg-blue-100 border-blue-300 text-blue-800"
                  : "border-gray-300 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Timeline Scrubber */}
      <div className="mb-4">
        <div
          className="relative h-2 bg-gray-200 rounded-full cursor-pointer"
          onClick={handleTimelineClick}
        >
          <div
            className="absolute top-0 left-0 h-full bg-blue-600 rounded-full transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
          <div
            className="absolute top-1/2 transform -translate-y-1/2 w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-md cursor-pointer"
            style={{ left: `calc(${progress}% - 8px)` }}
          />
        </div>
      </div>

      {/* Event Info */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>
            Event {currentEventIndex + 1} of {events.length}
          </span>
          {currentEvent && (
            <span className="font-medium">
              {currentEvent.stage} • {formatTime(currentEvent)}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <span>Duration: {formatDuration()}</span>
          {isPlaying && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-red-600 font-medium">PLAYING</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
