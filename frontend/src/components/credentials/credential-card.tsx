"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { KeyRound, Trash2, CheckCircle, ShieldCheck } from "lucide-react";
import { formatDate } from "@/lib/utils";
import apiClient from "@/lib/api-client";
import type { Credential } from "@/types";

interface CredentialCardProps {
  credential: Credential;
  onDelete: (id: string) => void;
  onVerified: () => void;
}

export function CredentialCard({ credential, onDelete, onVerified }: CredentialCardProps) {
  const [verifying, setVerifying] = useState(false);

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await apiClient.post(`/api/v1/credentials/${credential.id}/verify`);
      if (res.data.success) {
        onVerified();
      } else {
        alert(res.data.message);
      }
    } catch {
      alert("인증 테스트에 실패했습니다.");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div className="flex items-center gap-2">
          <KeyRound className="h-5 w-5 text-primary" />
          <CardTitle className="text-base">{credential.label}</CardTitle>
          {credential.is_verified && <Badge variant="success">인증됨</Badge>}
        </div>
        <Button variant="ghost" size="icon" onClick={() => onDelete(credential.id)}>
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm text-muted-foreground">
          <p>Client ID: {credential.naver_client_id}</p>
          <p>등록일: {formatDate(credential.created_at)}</p>
          {credential.last_verified_at && (
            <p>마지막 인증: {formatDate(credential.last_verified_at)}</p>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={handleVerify} disabled={verifying}>
          <ShieldCheck className="mr-2 h-4 w-4" />
          {verifying ? "테스트 중..." : "인증 테스트"}
        </Button>
      </CardContent>
    </Card>
  );
}
