/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api.cgi',
        destination: 'http://localhost:3001/api.cgi'
      },
      {
        source: '/files/:path*',
        destination: 'http://localhost:3001/files/:path*'
      },
      {
        source: '/file/:filename',
        destination: 'http://localhost:3001/file/:filename'
      }
    ];
  }
};
export default nextConfig;
