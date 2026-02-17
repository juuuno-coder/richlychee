"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListTodo,
  KeyRound,
  Package,
  Settings,
  Cherry,
  Globe,
  CreditCard,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "대시보드", icon: LayoutDashboard },
  { href: "/crawl", label: "크롤링", icon: Globe },
  { href: "/jobs", label: "작업 관리", icon: ListTodo },
  { href: "/credentials", label: "API 자격증명", icon: KeyRound },
  { href: "/products", label: "등록 상품", icon: Package },
  { href: "/subscription", label: "구독 요금제", icon: CreditCard },
  { href: "/settings", label: "설정", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 border-r bg-card lg:block">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center border-b px-6">
          <Link href="/dashboard" className="flex items-center gap-2 font-bold text-lg">
            <Cherry className="h-6 w-6 text-red-500" />
            Richlychee
          </Link>
        </div>
        <nav className="flex-1 space-y-1 p-4">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
