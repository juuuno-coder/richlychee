import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function proxyRequest(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join("/");
  const search = request.nextUrl.search;
  const targetUrl = `${BACKEND_URL}/api/v1/${path}${search}`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!["host", "connection"].includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const body = hasBody ? request.body : undefined;

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
    // @ts-ignore
    duplex: "half",
  });

  const responseHeaders = new Headers();
  response.headers.forEach((value, key) => {
    if (!["transfer-encoding"].includes(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: responseHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
