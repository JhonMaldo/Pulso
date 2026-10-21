import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.endsWith('/KB_limpio.json')) return 'knowledge-base';
        },
      },
    },
  },
});
