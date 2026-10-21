import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { PAGES, renderPageHtml } from "./src/seo.js";

// Pré-génère un HTML par route publique (title/description/OG/canonical propres),
// pour que les crawlers sans JS voient les bonnes métadonnées.
function prerenderMeta() {
  let outDir;
  return {
    name: "rimbot-prerender-meta",
    apply: "build",
    configResolved(config) {
      outDir = resolve(config.root, config.build.outDir);
    },
    closeBundle() {
      const html = readFileSync(resolve(outDir, "index.html"), "utf8");
      for (const [path, page] of Object.entries(PAGES)) {
        if (page.file) writeFileSync(resolve(outDir, page.file), renderPageHtml(html, path));
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), prerenderMeta()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY || "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
    css: false,
  },
});
