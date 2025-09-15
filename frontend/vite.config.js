import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Set base for GitHub Pages under repository path
const base = '/hermes-agent/';

export default defineConfig({
  plugins: [react()],
  base,
  define: {
    // Expose environment variables to the client
    'import.meta.env.VITE_BACKEND_URL': JSON.stringify(process.env.VITE_BACKEND_URL || ''),
    'import.meta.env.VITE_BACKEND_WS_URL': JSON.stringify(process.env.VITE_BACKEND_WS_URL || ''),
    'import.meta.env.VITE_ENVIRONMENT': JSON.stringify(process.env.VITE_ENVIRONMENT || 'development'),
  },
});
