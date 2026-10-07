import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': apiProxyTarget,
      // Must stay in sync with the follow-link pattern in backend/config/urls.py.
      '^/[A-Za-z0-9]+$': apiProxyTarget,
    },
  },
});
