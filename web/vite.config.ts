import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/webhooks": "http://127.0.0.1:5000",
      "/trigger_outage": "http://127.0.0.1:5000",
      "/health": "http://127.0.0.1:5000",
      "/ready": "http://127.0.0.1:5000",
      "/socket.io": {
        target: "http://127.0.0.1:5000",
        ws: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
