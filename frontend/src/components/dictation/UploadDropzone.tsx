import { UploadCloud } from "lucide-react";
import { useCallback, useRef, useState } from "react";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const ACCEPTED_FORMATS = [".wav", ".mp3", ".m4a", ".webm", ".ogg", ".aac", ".flac"];

export function UploadDropzone({ onFileSelected, disabled }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled) setIsDragging(true);
    },
    [disabled],
  );

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      const file = e.dataTransfer.files?.[0];
      if (file) {
        setSelectedFile(file);
        onFileSelected(file);
      }
    },
    [disabled, onFileSelected],
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      onFileSelected(file);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`group relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
        disabled
          ? "cursor-not-allowed bg-slate-50 opacity-60"
          : isDragging
            ? "border-emerald-500 bg-emerald-50/50"
            : "border-slate-300 bg-slate-50/50 hover:border-emerald-500 hover:bg-slate-50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_FORMATS.join(",")}
        disabled={disabled}
        onChange={handleFileChange}
        className="hidden"
      />

      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 transition-transform group-hover:scale-110">
        <UploadCloud className="h-6 w-6" />
      </div>

      <p className="mt-3 text-sm font-semibold text-slate-800">
        {selectedFile ? (
          <span className="text-emerald-700">{selectedFile.name}</span>
        ) : (
          "Tarik file audio ke sini, atau klik untuk memilih"
        )}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {selectedFile
          ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Klik untuk mengganti file`
          : "Format yang didukung: WAV (16 kHz disarankan), MP3, M4A, WebM, OGG (Maks 50 MB)"}
      </p>
    </div>
  );
}
