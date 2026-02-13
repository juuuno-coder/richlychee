"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import apiClient from "@/lib/api-client";

interface CredentialFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function CredentialForm({ onSuccess, onCancel }: CredentialFormProps) {
  const [label, setLabel] = useState("기본");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await apiClient.post("/api/v1/credentials", {
        label,
        naver_client_id: clientId,
        naver_client_secret: clientSecret,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || "등록에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="label">이름</Label>
        <Input id="label" value={label} onChange={(e) => setLabel(e.target.value)} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="clientId">Client ID</Label>
        <Input
          id="clientId"
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="clientSecret">Client Secret</Label>
        <Input
          id="clientSecret"
          type="password"
          value={clientSecret}
          onChange={(e) => setClientSecret(e.target.value)}
          required
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>취소</Button>
        <Button type="submit" disabled={loading}>
          {loading ? <LoadingSpinner className="h-4 w-4" /> : "등록"}
        </Button>
      </div>
    </form>
  );
}
