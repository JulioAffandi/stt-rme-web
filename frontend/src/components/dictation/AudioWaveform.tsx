interface AudioWaveformProps {
  level: number; // 0 - 100
  isRecording: boolean;
  isPaused: boolean;
}

export function AudioWaveform({ level, isRecording, isPaused }: AudioWaveformProps) {
  // Buat 16 bar visualisasi
  const barCount = 18;
  const bars = Array.from({ length: barCount }, (_, i) => {
    if (!isRecording || isPaused) return 6; // tinggi minimal saat jeda/idle
    // variasi ketinggian berbasis level dan indeks bar
    const centerFactor = 1 - Math.abs(i - barCount / 2) / (barCount / 2);
    const randomized = Math.sin(i * 1.3 + level * 0.1) * 0.3 + 0.7;
    const height = Math.max(6, Math.min(48, Math.round(level * centerFactor * randomized * 0.5 + 8)));
    return height;
  });

  return (
    <div className="flex h-16 w-full items-center justify-center gap-1.5 rounded-lg bg-slate-900/90 px-4 py-2">
      {bars.map((h, i) => (
        <span
          key={i}
          style={{ height: `${h}px` }}
          className={`w-1.5 rounded-full transition-all duration-75 ${
            isPaused
              ? "bg-amber-400/60"
              : isRecording
                ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"
                : "bg-slate-600"
          }`}
        />
      ))}
    </div>
  );
}
