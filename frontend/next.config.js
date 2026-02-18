/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) return [];
    const base = apiUrl.startsWith('http') ? apiUrl : `https://${apiUrl}`;
    return [{ source: '/api/proxy/:path*', destination: `${base}/:path*` }];
  },
};

module.exports = nextConfig;
