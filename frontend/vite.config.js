// Vite build config for the Hone frontend.
//
// - `npm run dev`   serves the app on :5173 and proxies /api to the Python
//                   server on :8000 (start it with `python -m hone serve`).
// - `npm run build` writes the production bundle straight into
//                   hone/web/static/, which is what FastAPI serves. The built
//                   files are committed so Docker/Render/Fly deploys need no
//                   Node toolchain.
//
// Everything in frontend/public/ (favicons, og.png, config.js, robots.txt)
// is copied verbatim into the build output.
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

const here = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: `${here}../hone/web/static`,
    emptyOutDir: true,
    assetsDir: 'assets',
    // The docs are bundled as text so Methodology/Backtests render offline.
    chunkSizeWarningLimit: 1200,
  },
  server: {
    port: 5173,
    // The docs/ and research/ folders live outside frontend/; allow reading them.
    fs: { allow: ['..'] },
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
});
