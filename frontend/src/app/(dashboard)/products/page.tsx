"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/common/empty-state";
import { useCredentials } from "@/hooks/use-credentials";
import apiClient from "@/lib/api-client";
import { Search } from "lucide-react";
import type { Credential } from "@/types";

export default function ProductsPage() {
  const { credentials } = useCredentials();
  const [selectedCred, setSelectedCred] = useState("");
  const [keyword, setKeyword] = useState("");
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!selectedCred) return;
    setLoading(true);
    try {
      const res = await apiClient.get("/api/v1/products", {
        params: { credential_id: selectedCred, product_name: keyword || undefined },
      });
      setProducts(res.data?.contents || []);
    } catch {
      alert("조회에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">등록 상품</h1>

      <Card>
        <CardContent className="flex gap-4 pt-6">
          <select
            className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={selectedCred}
            onChange={(e) => setSelectedCred(e.target.value)}
          >
            <option value="">자격증명 선택</option>
            {credentials.map((c: Credential) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>
          <Input
            placeholder="상품명 검색"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="max-w-xs"
          />
          <Button onClick={handleSearch} disabled={!selectedCred || loading}>
            <Search className="mr-2 h-4 w-4" />
            {loading ? "조회 중..." : "조회"}
          </Button>
        </CardContent>
      </Card>

      {products.length === 0 ? (
        <EmptyState title="조회 결과가 없습니다" description="자격증명을 선택하고 검색하세요." />
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              {products.map((p: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <span>{p.originProduct?.name || p.name || `상품 ${idx + 1}`}</span>
                  <span className="text-muted-foreground">
                    {p.channelProductNo || p.originProductNo || ""}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
