"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileSpreadsheet } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  disabled?: boolean;
}

export function FileUploadZone({ onFileSelect, selectedFile, disabled }: FileUploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "text/csv": [".csv"],
    },
    maxFiles: 1,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors cursor-pointer",
        isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50",
        disabled && "cursor-not-allowed opacity-50"
      )}
    >
      <input {...getInputProps()} />
      {selectedFile ? (
        <>
          <FileSpreadsheet className="h-12 w-12 text-green-600" />
          <p className="mt-4 text-sm font-medium">{selectedFile.name}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {(selectedFile.size / 1024).toFixed(1)} KB
          </p>
        </>
      ) : (
        <>
          <Upload className="h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-sm font-medium">
            {isDragActive ? "파일을 놓으세요" : "엑셀 파일을 드래그하거나 클릭하여 선택"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">.xlsx, .csv 파일 지원</p>
        </>
      )}
    </div>
  );
}
