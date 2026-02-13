import { useState } from "react";
import apiClient from "@/lib/api-client";
import type { Job } from "@/types";

interface UploadOptions {
  credentialId: string;
  dryRun: boolean;
}

export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = async (file: File, options: UploadOptions): Promise<Job | null> => {
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("credential_id", options.credentialId);
      formData.append("dry_run", String(options.dryRun));

      const res = await apiClient.post("/api/v1/jobs", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    } catch (err: any) {
      setError(err.response?.data?.detail || "업로드에 실패했습니다.");
      return null;
    } finally {
      setUploading(false);
    }
  };

  return { upload, uploading, error };
}
