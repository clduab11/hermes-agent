import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Set base for GitHub Pages under repository path
const base = '/hermes-agent/';

export default defineConfig({
  plugins: [react()],
  base,
});
