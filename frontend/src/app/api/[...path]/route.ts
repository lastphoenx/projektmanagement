import { NextRequest, NextResponse } from "next/server";

const API_INTERNAL = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";

async function proxyRequest(request: NextRequest, pathSegments: string[]) {
  const targetPath = `/api/${pathSegments.join("/")}`;
  const url = `${API_INTERNAL}${targetPath}${request.nextUrl.search}`;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const cookie = request.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);

  const forwardedProto =
    request.headers.get("x-forwarded-proto") ||
    request.nextUrl.protocol.replace(":", "") ||
    "http";
  headers.set("x-forwarded-proto", forwardedProto);
  const host = request.headers.get("host");
  if (host) headers.set("x-forwarded-host", host);

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.arrayBuffer() : undefined;

  const upstream = await fetch(url, {
    method: request.method,
    headers,
    body,
    redirect: "manual",
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (key.toLowerCase() === "set-cookie") return;
    responseHeaders.set(key, value);
  });

  for (const setCookie of upstream.headers.getSetCookie()) {
    responseHeaders.append("set-cookie", setCookie);
  }

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

type RouteContext = { params: Promise<{ path: string[] }> };

async function withPath(
  request: NextRequest,
  context: RouteContext
): Promise<NextResponse> {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export const GET = withPath;
export const POST = withPath;
export const PUT = withPath;
export const PATCH = withPath;
export const DELETE = withPath;
export const OPTIONS = withPath;
