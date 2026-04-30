import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const UNREACHABLE_MSG =
  "Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.";

async function proxy(
  req: NextRequest,
  ctx: { params: { path: string[] } },
): Promise<NextResponse> {
  const base = process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";
  const target = `${base}/${ctx.params.path.join("/")}`;
  const init: RequestInit = { method: req.method };
  const ct = req.headers.get("content-type");
  if (ct) {
    init.headers = { "content-type": ct };
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
