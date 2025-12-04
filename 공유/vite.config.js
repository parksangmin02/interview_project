import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // 프론트엔드가 실행될 포트
    proxy: {
      // '/api'로 시작하는 모든 요청을
      '/api': {
        // ◀◀ 백엔드 서버(127.0.0.1:5000)로 넘겨라
        target: 'http://127.0.0.1:5000', 
        changeOrigin: true, // CORS 문제 해결
      },
    },
  },
})