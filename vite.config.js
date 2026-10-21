import { defineConfig } from 'vite';

// En desarrollo, /api se manda al backend local (uvicorn en el puerto 8000).
export default defineConfig({
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
});
