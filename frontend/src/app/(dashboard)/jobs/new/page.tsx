"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileUploadZone } from "@/components/jobs/file-upload-zone";
import { ValidationResult } from "@/components/jobs/validation-result";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { useCredentials } from "@/hooks/use-credentials";
import apiClient from "@/lib/api-client";
import type { Job, Credential } from "@/types";
import { CheckCircle2 } from "lucide-react";

type Step = 1 | 2 | 3;

export default function NewJobPage() {
  const router = useRouter();
  const { credentials } = useCredentials();
  const [step, setStep] = useState<Step>(1);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [selectedCredential, setSelectedCredential] = useState<string>("");
  const [dryRun, setDryRun] = useState(false);
  const [starting, setStarting] = useState(false);

  const handleUpload = async () => {
    if (!file || !selectedCredential) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("credential_id", selectedCredential);
      formData.append("dry_run", String(dryRun));

      const res = await apiClient.post("/api/v1/jobs", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setJob(res.data);
      if (res.data.status === "PENDING") {
        setStep(3);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "업로드에 실패했습니다.");
    } finally {
      setUploading(false);
    }
  };

  const handleStart = async () => {
    if (!job) return;
    setStarting(true);
    try {
      await apiClient.post(`/api/v1/jobs/${job.id}/start`);
      router.push(`/jobs/${job.id}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || "작업 시작에 실패했습니다.");
      setStarting(false);
    }
  };

  const steps = [
    { num: 1, label: "파일 업로드" },
    { num: 2, label: "설정" },
    { num: 3, label: "확인 및 실행" },
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-3xl font-bold">새 작업</h1>

      {/* 스테퍼 */}
      <div className="flex items-center justify-center gap-4">
        {steps.map((s, i) => (
          <div key={s.num} className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                step >= s.num
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {step > s.num ? <CheckCircle2 className="h-4 w-4" /> : s.num}
            </div>
            <span className={`text-sm ${step >= s.num ? "font-medium" : "text-muted-foreground"}`}>
              {s.label}
            </span>
            {i < steps.length - 1 && <div className="h-px w-8 bg-border" />}
          </div>
        ))}
      </div>

      {/* Step 1: 파일 업로드 */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>엑셀 파일 업로드</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <FileUploadZone onFileSelect={setFile} selectedFile={file} />
            <Button className="w-full" disabled={!file} onClick={() => setStep(2)}>
              다음
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: 설정 */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>작업 설정</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">API 자격증명</label>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={selectedCredential}
                onChange={(e) => setSelectedCredential(e.target.value)}
              >
                <option value="">선택하세요</option>
                {credentials.map((c: Credential) => (
                  <option key={c.id} value={c.id}>
                    {c.label} ({c.naver_client_id})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="dryRun"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="dryRun" className="text-sm">
                테스트 모드 (실제 등록 안 함)
              </label>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)}>이전</Button>
              <Button
                className="flex-1"
                disabled={!selectedCredential || uploading}
                onClick={handleUpload}
              >
                {uploading ? <LoadingSpinner className="h-4 w-4" /> : "업로드 및 검증"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: 확인 및 실행 */}
      {step === 3 && job && (
        <div className="space-y-4">
          {job.validation_errors || job.validation_warnings ? (
            <ValidationResult
              totalRows={job.total_rows}
              errors={job.validation_errors || []}
              warnings={job.validation_warnings || []}
            />
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>작업 요약</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>파일: {job.original_filename}</p>
              <p>총 행: {job.total_rows}</p>
              <p>모드: {job.dry_run ? "테스트" : "실제 등록"}</p>
            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setStep(2)}>이전</Button>
            <Button
              className="flex-1"
              disabled={starting || job.status === "FAILED"}
              onClick={handleStart}
            >
              {starting ? <LoadingSpinner className="h-4 w-4" /> : "등록 시작"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
