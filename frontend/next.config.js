/** @type {import('next').NextConfig} */

// When deploying to a GitHub Pages *project* site (username.github.io/RepoName/),
// the app is served from a subpath, not the domain root. Set
// NEXT_PUBLIC_BASE_PATH=/RepoName at build time to handle that; leave it
// unset for a custom domain, a GitHub Pages *user/org* site, Vercel, or
// Netlify, where the app is served from the root.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    // next/image's optimizer needs a server; static export doesn't have
    // one, so images are served as-is.
    unoptimized: true,
  },
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
};

module.exports = nextConfig;
