import { defineConfig } from 'vite';

// Le jeu compilé va directement dans le site SensAI : frontend/public/games/gardien-chateau/
export default defineConfig({
  base: './',
  build: {
    outDir: '../../frontend/public/games/gardien-chateau',
    emptyOutDir: true,
    chunkSizeWarningLimit: 2500,
  },
});
