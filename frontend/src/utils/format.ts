export function formatTimestamp(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds - Math.floor(seconds)) * 10);
  
  const mStr = String(mins).padStart(2, '0');
  const sStr = String(secs).padStart(2, '0');
  
  if (ms > 0) {
    return `${mStr}:${sStr}.${ms}`;
  }
  return `${mStr}:${sStr}`;
}

export function formatDuration(seconds: number): string {
  if (isNaN(seconds) || seconds <= 0) return '0s';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs}s`;
}
