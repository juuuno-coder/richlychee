"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CredentialCard } from "@/components/credentials/credential-card";
import { CredentialForm } from "@/components/credentials/credential-form";
import { EmptyState } from "@/components/common/empty-state";
import { PageLoading } from "@/components/common/loading-spinner";
import { useCredentials } from "@/hooks/use-credentials";
import apiClient from "@/lib/api-client";
import { Plus } from "lucide-react";

export default function CredentialsPage() {
  const { credentials, isLoading, mutate } = useCredentials();
  const [dialogOpen, setDialogOpen] = useState(false);

  if (isLoading) return <PageLoading />;

  const handleDelete = async (id: string) => {
    if (!confirm("이 자격증명을 삭제하시겠습니까?")) return;
    await apiClient.delete(`/api/v1/credentials/${id}`);
    mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">API 자격증명</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />추가
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>새 자격증명 등록</DialogTitle>
            </DialogHeader>
            <CredentialForm
              onSuccess={() => {
                setDialogOpen(false);
                mutate();
              }}
              onCancel={() => setDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      {credentials.length === 0 ? (
        <EmptyState
          title="자격증명이 없습니다"
          description="네이버 커머스 API 자격증명을 등록하세요."
          action={
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />첫 번째 자격증명 등록
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {credentials.map((cred) => (
            <CredentialCard
              key={cred.id}
              credential={cred}
              onDelete={handleDelete}
              onVerified={() => mutate()}
            />
          ))}
        </div>
      )}
    </div>
  );
}
