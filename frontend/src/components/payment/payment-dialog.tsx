"use client";

import { useState } from "react";
import { paymentApi } from "@/lib/api-client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { CreditCard } from "lucide-react";

declare global {
  interface Window {
    PortOne?: {
      requestPayment: (options: any) => Promise<any>;
    };
  }
}

interface PaymentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  plan: {
    id: string;
    name: string;
    display_name: string;
    price_monthly: number;
    price_yearly: number;
  };
  onSuccess: () => void;
}

export function PaymentDialog({ open, onOpenChange, plan, onSuccess }: PaymentDialogProps) {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [loading, setLoading] = useState(false);

  const amount = billingCycle === "monthly" ? plan.price_monthly : plan.price_yearly;

  const handlePayment = async () => {
    if (!window.PortOne) {
      alert("결제 모듈 로딩 중입니다. 잠시 후 다시 시도해주세요.");
      return;
    }

    setLoading(true);
    try {
      // 1. 결제 준비 API 호출
      const prepareRes = await paymentApi.prepare(plan.id, billingCycle);
      const { order_id, payment_id, amount, currency, plan_name, customer_name, customer_email } =
        prepareRes.data;

      // 2. PortOne v2 결제창 호출
      const portoneRes = await window.PortOne.requestPayment({
        storeId: process.env.NEXT_PUBLIC_PORTONE_STORE_ID, // PortOne 스토어 ID
        channelKey: process.env.NEXT_PUBLIC_PORTONE_CHANNEL_KEY, // 채널 키
        paymentId: order_id,
        orderName: `${plan_name} - ${billingCycle === "monthly" ? "월간" : "연간"} 구독`,
        totalAmount: amount,
        currency: currency,
        payMethod: "CARD",
        customer: {
          fullName: customer_name,
          email: customer_email,
        },
      });

      // 3. 결제 결과 확인
      if (portoneRes.code != null) {
        // 결제 실패
        alert(`결제 실패: ${portoneRes.message}`);
        setLoading(false);
        return;
      }

      // 4. 결제 검증 API 호출
      const verifyRes = await paymentApi.verify(payment_id, portoneRes.paymentId);

      if (verifyRes.data.success) {
        alert("결제가 완료되었습니다!");
        onSuccess();
        onOpenChange(false);
      } else {
        alert(`결제 검증 실패: ${verifyRes.data.message}`);
      }
    } catch (error: any) {
      console.error("결제 오류:", error);
      alert(error.response?.data?.detail || "결제 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            구독 결제
          </DialogTitle>
          <DialogDescription>
            {plan.display_name} 플랜 결제를 진행합니다
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* 결제 주기 선택 */}
          <div>
            <Label className="text-base font-semibold mb-3 block">결제 주기</Label>
            <RadioGroup value={billingCycle} onValueChange={(value) => setBillingCycle(value as any)}>
              <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-accent cursor-pointer">
                <RadioGroupItem value="monthly" id="monthly" />
                <Label htmlFor="monthly" className="flex-1 cursor-pointer">
                  <div className="font-medium">월간 결제</div>
                  <div className="text-sm text-muted-foreground">
                    매월 {plan.price_monthly.toLocaleString()}원
                  </div>
                </Label>
                <div className="font-bold text-lg">{plan.price_monthly.toLocaleString()}원</div>
              </div>

              <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-accent cursor-pointer">
                <RadioGroupItem value="yearly" id="yearly" />
                <Label htmlFor="yearly" className="flex-1 cursor-pointer">
                  <div className="font-medium">연간 결제</div>
                  <div className="text-sm text-muted-foreground">
                    1년간 {plan.price_yearly.toLocaleString()}원 (2개월 할인)
                  </div>
                </Label>
                <div className="font-bold text-lg">{plan.price_yearly.toLocaleString()}원</div>
              </div>
            </RadioGroup>
          </div>

          {/* 결제 금액 요약 */}
          <div className="bg-muted p-4 rounded-lg space-y-2">
            <div className="flex justify-between text-sm">
              <span>플랜</span>
              <span className="font-medium">{plan.display_name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>결제 주기</span>
              <span className="font-medium">
                {billingCycle === "monthly" ? "월간" : "연간"}
              </span>
            </div>
            <div className="pt-2 border-t flex justify-between">
              <span className="font-semibold">총 결제 금액</span>
              <span className="font-bold text-lg text-primary">
                {amount.toLocaleString()}원
              </span>
            </div>
          </div>

          {/* 결제 버튼 */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="flex-1"
              disabled={loading}
            >
              취소
            </Button>
            <Button onClick={handlePayment} className="flex-1" disabled={loading}>
              {loading ? (
                <>
                  <LoadingSpinner className="mr-2" />
                  결제 처리 중...
                </>
              ) : (
                <>
                  <CreditCard className="mr-2 h-4 w-4" />
                  결제하기
                </>
              )}
            </Button>
          </div>

          <p className="text-xs text-muted-foreground text-center">
            결제는 안전하게 암호화되어 처리됩니다.
            <br />
            결제 후 즉시 플랜이 활성화됩니다.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
