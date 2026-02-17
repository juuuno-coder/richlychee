"use client";

import { useEffect, useState } from "react";
import { subscriptionApi } from "@/lib/api-client";
import { UsageStats as UsageStatsType } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrendingUp, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export default function UsageStats() {
  const router = useRouter();
  const [stats, setStats] = useState<UsageStatsType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const res = await subscriptionApi.getUsage();
      setStats(res.data);
    } catch (error) {
      console.error("사용량 조회 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) {
    return null;
  }

  const mainFeatures = [
    { key: "crawl_jobs_per_month", name: "월 크롤링" },
    { key: "product_registrations_per_month", name: "월 상품 등록" },
    { key: "stored_products", name: "저장 상품" },
  ];

  const isNearLimit = (percent: number) => percent >= 80;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>구독 플랜 및 사용량</CardTitle>
            <CardDescription>
              {stats.plan.display_name} 플랜
              {stats.plan.is_popular && (
                <Badge variant="secondary" className="ml-2">
                  인기
                </Badge>
              )}
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => router.push("/subscription")}>
            <TrendingUp className="w-4 h-4 mr-2" />
            플랜 변경
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {mainFeatures.map(({ key, name }) => {
          const feature = stats.features[key];
          if (!feature) return null;

          const nearLimit = isNearLimit(feature.usage_percent);

          return (
            <div key={key}>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium flex items-center gap-2">
                  {name}
                  {nearLimit && (
                    <AlertCircle className="w-4 h-4 text-yellow-500" />
                  )}
                </span>
                <span className="text-muted-foreground">
                  {feature.current} / {feature.limit === -1 ? "무제한" : feature.limit}
                </span>
              </div>
              <Progress
                value={feature.usage_percent}
                className="h-2"
              />
              {nearLimit && feature.limit !== -1 && (
                <p className="text-xs text-yellow-600 mt-1">
                  ⚠️ 제한의 80% 이상 사용 중입니다
                </p>
              )}
            </div>
          );
        })}

        <div className="pt-2 border-t">
          <p className="text-xs text-muted-foreground">
            사용량 리셋: {new Date(stats.usage_reset_at).toLocaleDateString()}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
