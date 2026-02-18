"use client";

import { useEffect, useState } from "react";
import { crawlApi } from "@/lib/api-client";
import { CrawlJob, CrawlPreset } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Globe, Play, X, Trash2, ExternalLink, Search } from "lucide-react";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { useRouter } from "next/navigation";

export default function CrawlPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [jobs, setJobs] = useState<CrawlJob[]>([]);
  const [presets, setPresets] = useState<CrawlPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [crawling, setCrawling] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [jobsRes, presetsRes] = await Promise.all([
        crawlApi.listJobs({ size: 50 }),
        crawlApi.getPresets(),
      ]);
      setJobs(jobsRes.data.items || []);
      setPresets(presetsRes.data.presets || []);
    } catch (error) {
      console.error("데이터 로드 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickCrawl = async () => {
    if (!url.trim()) {
      alert("URL을 입력해주세요.");
      return;
    }

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      alert("유효한 URL을 입력해주세요 (http:// 또는 https://)");
      return;
    }

    setCrawling(true);
    try {
      const res = await crawlApi.quickCrawl(url, true);
      alert(`크롤링이 시작되었습니다!\n감지된 사이트: ${res.data.detected_site || "알 수 없음"}`);
      setUrl("");
      await loadData();
    } catch (error: any) {
      if (error.response?.status === 402) {
        alert("구독 플랜 제한에 도달했습니다.\n플랜을 업그레이드해주세요.");
      } else {
        alert(error.response?.data?.detail || "크롤링 시작에 실패했습니다.");
      }
    } finally {
      setCrawling(false);
    }
  };

  const handleCancelJob = async (id: string) => {
    if (!confirm("이 작업을 취소하시겠습니까?")) return;

    try {
      await crawlApi.cancelJob(id);
      await loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "작업 취소에 실패했습니다.");
    }
  };

  const handleDeleteJob = async (id: string) => {
    if (!confirm("이 작업을 삭제하시겠습니까?")) return;

    try {
      await crawlApi.deleteJob(id);
      await loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "작업 삭제에 실패했습니다.");
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      PENDING: "secondary",
      RUNNING: "default",
      COMPLETED: "outline",
      FAILED: "destructive",
      CANCELLED: "secondary",
    };
    return <Badge variant={variants[status] || "secondary"}>{status}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* 원클릭 크롤링 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            원클릭 크롤링
          </CardTitle>
          <CardDescription>
            쇼핑몰 URL을 입력하면 자동으로 상품 정보를 수집합니다
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="url"
              placeholder="https://www.coupang.com/products?q=키보드"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleQuickCrawl()}
              disabled={crawling}
            />
            <Button onClick={handleQuickCrawl} disabled={crawling || !url.trim()}>
              {crawling ? (
                <>
                  <LoadingSpinner className="mr-2" />
                  크롤링 중...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  크롤링 시작
                </>
              )}
            </Button>
          </div>

          {/* 지원하는 쇼핑몰 */}
          {presets.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">지원하는 쇼핑몰:</p>
              <div className="flex flex-wrap gap-2">
                {presets.map((preset) => (
                  <Badge key={preset.id} variant="outline" className="cursor-pointer hover:bg-accent"
                    onClick={() => setUrl(preset.site_url)}
                  >
                    {preset.name}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 크롤링 작업 목록 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>크롤링 작업</CardTitle>
              <CardDescription>최근 크롤링 작업 내역</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadData}>
              새로고침
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>아직 크롤링 작업이 없습니다</p>
              <p className="text-sm mt-1">위에서 URL을 입력하여 크롤링을 시작하세요</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>상태</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>진행률</TableHead>
                    <TableHead>타입</TableHead>
                    <TableHead>생성일</TableHead>
                    <TableHead className="text-right">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell>{getStatusBadge(job.status)}</TableCell>
                      <TableCell>
                        <a
                          href={job.target_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline flex items-center gap-1 max-w-xs truncate"
                        >
                          {job.target_url}
                          <ExternalLink className="w-3 h-3 flex-shrink-0" />
                        </a>
                      </TableCell>
                      <TableCell>
                        {job.total_items > 0 ? (
                          <span className="text-sm">
                            {job.crawled_items} / {job.total_items}
                            <span className="text-muted-foreground ml-1">
                              ({Math.round((job.crawled_items / job.total_items) * 100)}%)
                            </span>
                          </span>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {job.target_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(job.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          {job.status === "COMPLETED" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => router.push(`/crawl/${job.id}`)}
                            >
                              결과 보기
                            </Button>
                          )}
                          {job.status === "RUNNING" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCancelJob(job.id)}
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          )}
                          {(job.status === "COMPLETED" || job.status === "FAILED") && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteJob(job.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
