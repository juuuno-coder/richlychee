"""구독 요금제 API 테스트."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_subscription_apis():
    """구독 요금제 API 테스트."""
    print("=" * 60)
    print("구독 요금제 API 테스트")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. 로그인
        email = "testuser@richlychee.com"
        password = "Test1234!@"

        resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 플랜 목록 조회
        print("\n[1] 플랜 목록 조회")
        resp = await client.get(f"{BASE_URL}/subscriptions/plans")
        plans = resp.json()
        print(f"   ✓ GET /subscriptions/plans: {resp.status_code}")
        print(f"   {len(plans)}개의 플랜:")
        for plan in plans:
            print(f"      [{plan['display_name']}] {plan['price_monthly']:,}원/월")
            print(f"        - 월 크롤링: {plan['limits']['crawl_jobs_per_month']}회")
            print(f"        - 월 등록: {plan['limits']['product_registrations_per_month']}개")

        # 3. 내 구독 정보 조회
        print("\n[2] 내 구독 정보")
        resp = await client.get(f"{BASE_URL}/subscriptions/my", headers=headers)
        if resp.status_code == 200:
            sub = resp.json()
            print(f"   ✓ GET /subscriptions/my: {resp.status_code}")
            print(f"   현재 플랜: {sub['plan']['display_name']}")
            print(f"   상태: {sub['status']}")
            print(f"   주기: {sub['billing_cycle']}")
        else:
            print(f"   ✗ GET /subscriptions/my: {resp.status_code}")

        # 4. 사용량 통계 조회
        print("\n[3] 사용량 통계")
        resp = await client.get(f"{BASE_URL}/subscriptions/usage", headers=headers)
        if resp.status_code == 200:
            usage = resp.json()
            print(f"   ✓ GET /subscriptions/usage: {resp.status_code}")
            print(f"   플랜: {usage['plan']['display_name']}")
            for feature, info in list(usage['features'].items())[:3]:
                print(f"      {feature}: {info['current']}/{info['limit']} ({info['usage_percent']}%)")
        else:
            print(f"   ✗ GET /subscriptions/usage: {resp.status_code}")

        # 5. 크롤링 작업 생성 (제한 테스트)
        print("\n[4] 크롤링 작업 생성 (제한 테스트)")
        resp = await client.post(
            f"{BASE_URL}/crawl-jobs",
            headers=headers,
            json={
                "target_url": "https://example.com/products",
                "target_type": "static",
                "crawl_config": {
                    "item_selector": ".product"
                }
            }
        )
        if resp.status_code == 201:
            print(f"   ✓ POST /crawl-jobs: {resp.status_code} (작업 생성 성공)")
        elif resp.status_code == 402:
            print(f"   ✓ POST /crawl-jobs: {resp.status_code} (제한 도달)")
            print(f"      {resp.json().get('detail')}")
        else:
            print(f"   ? POST /crawl-jobs: {resp.status_code}")

        # 6. 사용량 다시 확인
        print("\n[5] 사용량 재확인")
        resp = await client.get(f"{BASE_URL}/subscriptions/usage", headers=headers)
        if resp.status_code == 200:
            usage = resp.json()
            crawl_usage = usage['features'].get('crawl_jobs_per_month', {})
            print(f"   월 크롤링: {crawl_usage.get('current', 0)}/{crawl_usage.get('limit', 0)}")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_subscription_apis())
