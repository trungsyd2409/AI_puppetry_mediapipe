import { defineConfig } from "vite";

export default defineConfig({
  base: "./",            // relative paths so dist/ works from any sub-folder or iframe
  server: { host: true, port: 5173 },
  build: { target: "es2022", assetsDir: "app", chunkSizeWarningLimit: 2000 },
});
