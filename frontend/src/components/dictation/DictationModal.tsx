import {
  AlertCircle,
  Mic,
  Pause,
  Play,
  RotateCcw,
  Sparkles,
  Square,
  Upload,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
  useDictationJob,
  useTriggerSampleDictation,
  useUploadDictation,
} from "@/hooks/useDictation";
import { useRecorder } from "@/hooks/useRecorder";
import { cn } from "@/lib/utils";
import type { DictationSample, MappedFormResult } from "@/types";

import { AudioWaveform } from "./AudioWaveform";
import { JobProgressStepper } from "./JobProgressStepper";
import { ReviewPanel } from "./ReviewPanel";
import { SamplePicker } from "./SamplePicker";
import { UploadDropzone } from "./UploadDropzone";

interface DictationModalProps {
  open: boolean;
  onClose: () => void;
  encounterId: number;
  onApplyTranscript?: (transcript: string) => void;
  onApplyMappedForm?: (mapped: MappedFormResult, transcript: string) => void;
}

type InputMode = "record" | "upload" | "sample";

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const hundredths = Math.floor((ms % 1000) / 10);
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${pad(minutes)}:${pad(seconds)}.${pad(hundredths)}`;
}

export function DictationModal({
  open,
  onClose,
  encounterId,
  onApplyTranscript,
  onApplyMappedForm,
}: DictationModalProps) {
  const [mode, setMode] = useState<InputMode>("record");
  const [selectedUploadFile, setSelectedUploadFile] = useState<File | null>(null);
  const [selectedUploadUrl, setSelectedUploadUrl] = useState<string | null>(null);

  const [activeJobId, setActiveJobId] = useState<number | null>(null);

  // Recorder hook
  const {
    status: recStatus,
    durationMs,
    audioLevel,
    audioBlob,
    audioUrl: recAudioUrl,
    error: recError,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    resetRecording,
  } = useRecorder();

  // Mutations & polling query
  const uploadMutation = useUploadDictation(encounterId);
  const sampleMutation = useTriggerSampleDictation(encounterId);
  const { data: jobData } = useDictationJob(activeJobId);

  // Handle upload file selection
  function handleFileSelected(file: File) {
    setSelectedUploadFile(file);
    if (selectedUploadUrl) URL.revokeObjectURL(selectedUploadUrl);
    setSelectedUploadUrl(URL.createObjectURL(file));
  }

  // Submit audio rekaman atau upload ke backend
  async function handleSubmitAudio() {
    let fileToUpload: Blob | File | null = null;
    let filename = "recording.webm";

    if (mode === "record" && audioBlob) {
      fileToUpload = audioBlob;
      filename = `mic_${Date.now()}.webm`;
    } else if (mode === "upload" && selectedUploadFile) {
      fileToUpload = selectedUploadFile;
      filename = selectedUploadFile.name;
    }

    if (!fileToUpload) return;

    try {
      const resp = await uploadMutation.mutateAsync({
        file: fileToUpload,
        filename,
      });
      setActiveJobId(resp.job_id);
    } catch {
      // Error ditangani via state mutation
    }
  }

  // Submit via sampel audio
  async function handleSelectSample(sample: DictationSample) {
    try {
      const resp = await sampleMutation.mutateAsync(sample.id);
      setActiveJobId(resp.job_id);
    } catch {
      // Error ditangani
    }
  }

  // Reset all
  function handleReset() {
    resetRecording();
    setSelectedUploadFile(null);
    if (selectedUploadUrl) {
      URL.revokeObjectURL(selectedUploadUrl);
      setSelectedUploadUrl(null);
    }
    setActiveJobId(null);
  }

  function handleCloseModal() {
    if (recStatus === "recording" || recStatus === "paused") {
      stopRecording();
    }
    handleReset();
    onClose();
  }

  function handleApplyReview(mapped: MappedFormResult, transcript: string) {
    if (onApplyMappedForm) {
      onApplyMappedForm(mapped, transcript);
    } else if (onApplyTranscript) {
      onApplyTranscript(mapped.anamnesis || transcript);
    }
    handleCloseModal();
  }

  const isBusy =
    uploadMutation.isPending ||
    sampleMutation.isPending ||
    (activeJobId !== null &&
      jobData?.status !== "done" &&
      jobData?.status !== "error");

  const effectiveAudioUrl =
    recAudioUrl ||
    selectedUploadUrl ||
    (jobData?.audio_id ? `/api/v1/audio/${jobData.audio_id}` : null);

  return (
    <Modal
      open={open}
      onClose={handleCloseModal}
      title="Pencatatan Suara & Transkripsi Medis (Whisper STT)"
      className="max-w-2xl"
    >
      <div className="space-y-4">
        {/* Tab mode pilihan: Rekam / Upload / Contoh */}
        <div className="flex rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs font-semibold">
          <button
            type="button"
            disabled={isBusy || recStatus !== "idle"}
            onClick={() => setMode("record")}
            className={cn(
              "flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 transition-all",
              mode === "record"
                ? "bg-white text-emerald-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900",
            )}
          >
            <Mic className="h-3.5 w-3.5" />
            Rekam Langsung
          </button>
          <button
            type="button"
            disabled={isBusy || recStatus !== "idle"}
            onClick={() => setMode("upload")}
            className={cn(
              "flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 transition-all",
              mode === "upload"
                ? "bg-white text-emerald-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900",
            )}
          >
            <Upload className="h-3.5 w-3.5" />
            Unggah File Audio
          </button>
          <button
            type="button"
            disabled={isBusy || recStatus !== "idle"}
            onClick={() => setMode("sample")}
            className={cn(
              "flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 transition-all",
              mode === "sample"
                ? "bg-white text-emerald-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900",
            )}
          >
            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
            Contoh Dikte Sidang
          </button>
        </div>

        {/* Konten Tab 1: Perekam Mikrofon */}
        {mode === "record" && !activeJobId && (
          <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <AudioWaveform
              level={audioLevel}
              isRecording={recStatus === "recording"}
              isPaused={recStatus === "paused"}
            />

            <div className="flex items-center justify-between">
              <div className="font-mono text-2xl font-bold tracking-tight text-slate-800">
                {formatDuration(durationMs)}
              </div>
              <div className="flex items-center gap-2">
                {recStatus === "recording" && (
                  <Badge variant="destructive" className="animate-pulse">
                    Merekam...
                  </Badge>
                )}
                {recStatus === "paused" && (
                  <Badge variant="secondary" className="bg-amber-100 text-amber-800">
                    Dijeda
                  </Badge>
                )}
                {recStatus === "stopped" && (
                  <Badge variant="default" className="bg-emerald-600">
                    Selesai Direkam
                  </Badge>
                )}
              </div>
            </div>

            {recError && (
              <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{recError}</span>
              </div>
            )}

            {/* Tombol Kontrol Perekaman */}
            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              {recStatus === "idle" && (
                <Button
                  type="button"
                  onClick={startRecording}
                  className="bg-emerald-600 text-white hover:bg-emerald-700"
                >
                  <Mic className="mr-1.5 h-4 w-4" /> Mulai Rekam Dikte
                </Button>
              )}

              {recStatus === "recording" && (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={pauseRecording}
                    className="border-amber-300 text-amber-700 hover:bg-amber-50"
                  >
                    <Pause className="mr-1.5 h-4 w-4" /> Jeda
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={stopRecording}
                  >
                    <Square className="mr-1.5 h-4 w-4" /> Berhenti Rekam
                  </Button>
                </>
              )}

              {recStatus === "paused" && (
                <>
                  <Button
                    type="button"
                    onClick={resumeRecording}
                    className="bg-emerald-600 text-white hover:bg-emerald-700"
                  >
                    <Play className="mr-1.5 h-4 w-4" /> Lanjutkan
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={stopRecording}
                  >
                    <Square className="mr-1.5 h-4 w-4" /> Berhenti
                  </Button>
                </>
              )}

              {recStatus === "stopped" && (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={resetRecording}
                  >
                    <RotateCcw className="mr-1.5 h-4 w-4" /> Rekam Ulang
                  </Button>
                  <Button
                    type="button"
                    onClick={handleSubmitAudio}
                    disabled={uploadMutation.isPending}
                    className="bg-blue-600 text-white hover:bg-blue-700"
                  >
                    <Sparkles className="mr-1.5 h-4 w-4" /> Transkripsi Audio Ini
                  </Button>
                </>
              )}
            </div>
          </div>
        )}

        {/* Konten Tab 2: Upload File Audio */}
        {mode === "upload" && !activeJobId && (
          <div className="space-y-3">
            <UploadDropzone
              onFileSelected={handleFileSelected}
              disabled={uploadMutation.isPending}
            />
            {selectedUploadFile && (
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedUploadFile(null)}
                >
                  Batal
                </Button>
                <Button
                  type="button"
                  onClick={handleSubmitAudio}
                  disabled={uploadMutation.isPending}
                  className="bg-blue-600 text-white hover:bg-blue-700"
                >
                  <Sparkles className="mr-1.5 h-4 w-4" /> Transkripsikan File
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Konten Tab 3: Contoh Dikte Klinis untuk Sidang */}
        {mode === "sample" && !activeJobId && (
          <SamplePicker
            onSelectSample={handleSelectSample}
            disabled={sampleMutation.isPending}
          />
        )}

        {/* Tampilan Job Processing & Stepper */}
        {activeJobId && (
          <div className="space-y-4">
            <JobProgressStepper
              status={jobData?.status || "queued"}
              step={jobData?.step}
              error={jobData?.error}
            />

            {/* Panel Review Klinis & Supervisi Dokter (Fase 4, Bagian 4.2) */}
            {jobData?.status === "done" && jobData.result && (
              <ReviewPanel
                initialResult={jobData.result}
                audioUrl={effectiveAudioUrl}
                onApply={handleApplyReview}
                onCancel={handleReset}
              />
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
