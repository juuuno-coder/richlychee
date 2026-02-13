export { default } from "next-auth/middleware";

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/jobs/:path*",
    "/credentials/:path*",
    "/products/:path*",
    "/settings/:path*",
  ],
};
