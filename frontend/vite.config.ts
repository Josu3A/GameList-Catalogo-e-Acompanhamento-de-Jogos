import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Frontend em :5173 (origem já liberada no CORS/CSRF do backend — ver config/settings.py).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
