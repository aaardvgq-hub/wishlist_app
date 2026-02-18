/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return process.env.NEXT_PUBLIC_API_URL
      ? [{ source: '/api/proxy/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*` }]
      : [];
  },
};

module.exports = nextConfig;
