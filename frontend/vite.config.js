import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Set base for GitHub Pages under repository path
const base = '/hermes-agent/';

export default defineConfig({
  plugins: [react()],
  base,
  define: {
    // Expose environment variables to the client
    'import.meta.env.VITE_SOCKET_IO_URL': JSON.stringify(process.env.VITE_SOCKET_IO_URL || ''),
  },
});
