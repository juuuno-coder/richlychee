"use client";

import { useEffect, useState } from "react";
import { subscriptionApi } from "@/lib/api-client";
import { SubscriptionPlan, UserSubscription, UsageStats } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Check, Zap, TrendingUp } from "lucide-react";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { PaymentDialog } from "@/components/payment/payment-dialog";

export default function SubscriptionPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<UserSubscription | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [plansRes, subRes, usageRes] = await Promise.all([
        subscriptionApi.getPlans(),
        subscriptionApi.getMySubscription(),
        subscriptionApi.getUsage(),
      ]);
      setPlans(plansRes.data);
      setCurrentSubscription(subRes.data);
      setUsageStats(usageRes.data);
    } catch (error) {
      console.error("데이터 로드 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = (plan: SubscriptionPlan) => {
    // Free 플랜으로 다운그레이드는 바로 처리
    if (plan.price_monthly === 0) {
      if (confirm("무료 플랜으로 변경하시겠습니까?")) {
        downgradeTofree(plan.id);
      }
      return;
    }

    // 유료 플랜은 결제 다이얼로그 열기
    setSelectedPlan(plan);
    setPaymentDialogOpen(true);
  };

  const downgradeTofree = async (planId: string) => {
    try {
      await subscriptionApi.upgrade(planId, "monthly");
      alert("플랜이 변경되었습니다!");
      await loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "플랜 변경에 실패했습니다.");
    }
  };

  const handlePaymentSuccess = async () => {
    await loadData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 현재 구독 정보 */}
      {currentSubscription && usageStats && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>현재 플랜: {currentSubscription.plan.display_name}</CardTitle>
                <CardDescription>
                  {currentSubscription.plan.price_monthly > 0
                    ? `월 ${currentSubscription.plan.price_monthly.toLocaleString()}원`
                    : "무료"}
                </CardDescription>
              </div>
              <Badge variant={currentSubscription.status === "active" ? "default" : "secondary"}>
                {currentSubscription.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>사용량 리셋</span>
                  <span className="text-muted-foreground">
                    {new Date(usageStats.usage_reset_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* 주요 사용량 표시 */}
              <div className="grid gap-4">
                {Object.entries(usageStats.features).slice(0, 3).map(([key, data]) => (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="font-medium">
                        {key === "crawl_jobs_per_month" && "월 크롤링"}
                        {key === "product_registrations_per_month" && "월 상품 등록"}
                        {key === "stored_products" && "저장 상품"}
                      </span>
                      <span className="text-muted-foreground">
                        {data.current} / {data.limit === -1 ? "무제한" : data.limit}
                      </span>
                    </div>
                    <Progress value={data.usage_percent} className="h-2" />
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 플랜 목록 */}
      <div>
        <div className="mb-6">
          <h2 className="text-2xl font-bold">구독 플랜</h2>
          <p className="text-muted-foreground mt-1">비즈니스에 맞는 플랜을 선택하세요</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => {
            const isCurrent = currentSubscription?.plan.id === plan.id;

            return (
              <Card key={plan.id} className={plan.is_popular ? "border-primary shadow-lg" : ""}>
                <CardHeader>
                  {plan.is_popular && (
                    <Badge className="w-fit mb-2" variant="default">
                      <Zap className="w-3 h-3 mr-1" />
                      인기
                    </Badge>
                  )}
                  <CardTitle>{plan.display_name}</CardTitle>
                  <CardDescription className="min-h-[40px]">{plan.description}</CardDescription>
                  <div className="mt-4">
                    <span className="text-3xl font-bold">
                      {plan.price_monthly === 0
                        ? "무료"
                        : `₩${plan.price_monthly.toLocaleString()}`}
                    </span>
                    {plan.price_monthly > 0 && <span className="text-muted-foreground">/월</span>}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <FeatureItem
                      text={`월 크롤링 ${formatLimit(plan.limits.crawl_jobs_per_month)}회`}
                    />
                    <FeatureItem
                      text={`월 상품 등록 ${formatLimit(plan.limits.product_registrations_per_month)}개`}
                    />
                    <FeatureItem
                      text={`동시 크롤링 ${plan.limits.concurrent_crawls}개`}
                    />
                    <FeatureItem
                      text={`스케줄 ${formatLimit(plan.limits.schedules)}개`}
                    />
                    <FeatureItem
                      text={`가격 알림 ${formatLimit(plan.limits.price_alerts)}개`}
                    />
                    <FeatureItem
                      text={`저장 상품 ${formatLimit(plan.limits.stored_products)}개`}
                    />
                  </div>

                  <Button
                    className="w-full"
                    variant={isCurrent ? "outline" : plan.is_popular ? "default" : "outline"}
                    disabled={isCurrent}
                    onClick={() => handleUpgrade(plan)}
                  >
                    {isCurrent ? "현재 플랜" : "이 플랜 선택"}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* 연간 결제 안내 */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <TrendingUp className="w-6 h-6 text-primary mt-1" />
            <div>
              <h3 className="font-semibold mb-2">연간 결제로 절약하세요</h3>
              <p className="text-sm text-muted-foreground">
                연간 결제 시 2개월 무료! 최대 17% 할인 혜택을 받을 수 있습니다.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 결제 다이얼로그 */}
      {selectedPlan && (
        <PaymentDialog
          open={paymentDialogOpen}
          onOpenChange={setPaymentDialogOpen}
          plan={selectedPlan}
          onSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
}

function FeatureItem({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <Check className="w-4 h-4 text-primary flex-shrink-0" />
      <span>{text}</span>
    </div>
  );
}

function formatLimit(limit: number): string {
  return limit === -1 ? "무제한" : limit.toLocaleString();
}
