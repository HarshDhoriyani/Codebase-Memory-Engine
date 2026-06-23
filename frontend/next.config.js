/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: "/api/backend/:path*",
        headers: [
          { key: "Access-Control-Allow-Origin", value: "*" },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source:      "/api/backend/:path*",
        destination: "http://backend:8000/api/v1/:path*",
      },
    ];
  },
};

module.exports = nextConfig;