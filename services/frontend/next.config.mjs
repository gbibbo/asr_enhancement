/** @type {import('next').NextConfig} */
// Static export: the demo UI is served as pre-built static files by the FastAPI
// demo backend, behind the recruiter HTTPBasic gate, on a single origin. No Node
// server runs in production; the browser calls the backend directly at
// same-origin /demo/*.
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
