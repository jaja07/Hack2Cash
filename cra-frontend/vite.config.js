import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
    },
    // 🔥 Configuration pour Docker et hot-reload fiable
    watch: {
      usePolling: true,        // Essentiel pour Docker
      interval: 1000,          // Vérifie les changements toutes les 1s
    },
    hmr: {
      overlay: true,           // Affiche les erreurs dans le navigateur
      timeout: 5000,           // Timeout pour HMR
    },
    force: true,               // Force l'invalidation du cache au démarrage
  },

  build: {
    //outDir: '../cra-test-app/static',
    outDir: 'dist',
    emptyOutDir: true,
  },

  // 🔥 Optimisation des dépendances
  optimizeDeps: {
    force: true,               // Re-bundle les dépendances au démarrage
    include: ['react', 'react-dom', 'axios'], // Pré-bundle ces dépendances
  },

  // 🔥 Résolution des modules
  resolve: {
    alias: {
      // Évite les problèmes de résolution de modules
      '@': '/src',
    },
  },

  // 🔥 Cache-control pour le développement
  css: {
    devSourcemap: true,        // Sourcemaps pour faciliter le debug
  },
})