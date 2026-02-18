"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { crawlApi } from "@/lib/api-client";
import { CrawlJob, CrawledProduct } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Download, TrendingUp, Package } from "lucide-react";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export default function CrawlJobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [job, setJob] = useState<CrawlJob | null>(null);
  const [products, setProducts] = useState<CrawledProduct[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [showPriceAdjust, setShowPriceAdjust] = useState(false);
  const [adjustmentValue, setAdjustmentValue] = useState("10");

  useEffect(() => {
    loadData();
  }, [jobId]);

  const loadData = async () => {
    try {
      const [jobRes, productsRes] = await Promise.all([
        crawlApi.getJob(jobId),
        crawlApi.getJobProducts(jobId, { size: 100 }),
      ]);
      setJob(jobRes.data);
      setProducts(productsRes.data.items || []);
    } catch (error) {
      console.error("데이터 로드 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedProducts.size === products.length) {
      setSelectedProducts(new Set());
    } else {
      setSelectedProducts(new Set(products.map((p) => p.id)));
    }
  };

  const handleSelectProduct = (id: string) => {
    const newSelected = new Set(selectedProducts);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedProducts(newSelected);
  };

  const handleAdjustPrice = async () => {
    if (selectedProducts.size === 0) {
      alert("상품을 선택해주세요.");
      return;
    }

    const value = parseFloat(adjustmentValue);
    if (isNaN(value) || value <= 0) {
      alert("유효한 퍼센트 값을 입력해주세요.");
      return;
    }

    try {
      await crawlApi.adjustPrice(Array.from(selectedProducts), "percentage", value);
      alert("가격이 조정되었습니다!");
      setShowPriceAdjust(false);
      await loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "가격 조정에 실패했습니다.");
    }
  };

  const handleExport = async () => {
    try {
      const res = await crawlApi.export({ crawl_job_id: jobId });
      const blob = new Blob([res.data], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `crawled_products_${jobId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error: any) {
      alert(error.response?.data?.detail || "엑셀 내보내기에 실패했습니다.");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner />
      </div>
    );
  }

  if (!job) {
    return <div>작업을 찾을 수 없습니다.</div>;
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            뒤로
          </Button>
          <div>
            <h1 className="text-2xl font-bold">크롤링 결과</h1>
            <p className="text-sm text-muted-foreground mt-1">{job.target_url}</p>
          </div>
        </div>
        <Badge>{job.status}</Badge>
      </div>

      {/* 통계 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">전체 상품</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{job.total_items}개</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">성공</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{job.success_count}개</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">실패</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{job.failure_count}개</div>
          </CardContent>
        </Card>
      </div>

      {/* 상품 목록 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>크롤링된 상품 ({products.length})</CardTitle>
              <CardDescription>
                {selectedProducts.size > 0 && `${selectedProducts.size}개 선택됨`}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPriceAdjust(true)}
                disabled={selectedProducts.size === 0}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                가격 조정
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                엑셀 다운로드
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {products.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>크롤링된 상품이 없습니다</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b">
                <input
                  type="checkbox"
                  checked={selectedProducts.size === products.length}
                  onChange={handleSelectAll}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium">전체 선택</span>
              </div>

              <div className="space-y-2">
                {products.map((product) => (
                  <div
                    key={product.id}
                    className="flex items-start gap-4 p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedProducts.has(product.id)}
                      onChange={() => handleSelectProduct(product.id)}
                      className="w-4 h-4 mt-1"
                    />
                    {product.original_images[0] && (
                      <img
                        src={product.original_images[0]}
                        alt={product.original_title}
                        className="w-20 h-20 object-cover rounded"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate">{product.original_title}</h3>
                      <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                        <span>
                          {product.original_currency} {product.original_price.toLocaleString()}
                        </span>
                        {product.sale_price && product.sale_price !== product.original_price && (
                          <span className="text-primary font-medium">
                            → KRW {product.sale_price.toLocaleString()}
                          </span>
                        )}
                      </div>
                      {product.is_registered && (
                        <Badge variant="outline" className="mt-2">
                          등록 완료
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 가격 조정 다이얼로그 */}
      <Dialog open={showPriceAdjust} onOpenChange={setShowPriceAdjust}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>가격 조정</DialogTitle>
            <DialogDescription>
              선택한 {selectedProducts.size}개 상품의 가격을 일괄 조정합니다
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="adjustment">가격 인상률 (%)</Label>
              <Input
                id="adjustment"
                type="number"
                value={adjustmentValue}
                onChange={(e) => setAdjustmentValue(e.target.value)}
                placeholder="10"
                min="0"
                step="0.1"
              />
              <p className="text-sm text-muted-foreground">
                예: 10을 입력하면 원가의 10% 인상 (마진)
              </p>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowPriceAdjust(false)}>
              취소
            </Button>
            <Button onClick={handleAdjustPrice}>적용</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
