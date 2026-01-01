import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: "standalone",

  // Optional: Disable image optimization if not using Vercel
  // images: {
  //   unoptimized: true,
  // },
};

export default nextConfig;