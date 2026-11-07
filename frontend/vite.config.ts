import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { verifyAdapterPlugin } from './server/verifyAdapter.mjs'

export default defineConfig({
  plugins: [react(), verifyAdapterPlugin()],
  server: { host: '127.0.0.1', port: 5173, strictPort: true, cors: false },
})
