import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const UNREACHABLE_MSG =
  "Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.";

// Allowlist of request headers forwarded to the backend. Keeping this strict
// avoids leaking arbitrary client headers upstream. X-Demo-Session-Id is
// required by the demo backend (B10.2) for AssemblyAI uploads and must reach
// the upstream FastAPI app verbatim. We never log the header value here and
// never echo it back in the response.
const FORWARDED_REQUEST_HEADERS = ["content-type", "x-demo-session-id"] as const;

async function proxy(
  req: NextRequest,
  ctx: { params: { path: string[] } },
): Promise<NextResponse> {
  const base = process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";
  const target = `${base}/${ctx.params.path.join("/")}`;
  const init: RequestInit = { method: req.method };
  const forwarded: Record<string, string> = {};
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = req.headers.get(name);
    if (value) {
      forwarded[name] = value;
    }
  }
  if (Object.keys(forwarded).length > 0) {
    init.headers = forwarded;
  }
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }
  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch {
    return NextResponse.json({ detail: UNREACHABLE_MSG }, { status: 503 });
  }
  const buf = await upstream.arrayBuffer();
  const headers = new Headers();
  const upstreamCt = upstream.headers.get("content-type");
  if (upstreamCt) {
    headers.set("content-type", upstreamCt);
  }
  return new NextResponse(buf, { status: upstream.status, headers });
}

export const GET = proxy;
export const POST = proxy;
