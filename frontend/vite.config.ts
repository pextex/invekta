import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(({ mode }) => {
  const hosting = mode === "hosting";
  // Read only Codespaces metadata; never expose backend .env or credentials.
  const env = loadEnv(mode, process.cwd(), ["CODESPACE_NAME", "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"]);
  const name = env.CODESPACE_NAME;
  const domain = env.GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN || "app.github.dev";
  if ((name && !/^[a-zA-Z0-9-]+$/.test(name)) || !/^[a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*$/.test(domain)) {
    throw new Error("Neispravna Codespaces adresa pregleda.");
  }
  const host = name ? `${name}-5173.${domain}` : undefined;
  return {
    plugins: [react(), ...(hosting ? [{
      name: "company-hosting-entry",
      transformIndexHtml: { order: "pre" as const, handler(html: string) { return html.replace("/src/main.tsx", "/src/main.production.tsx"); } },
    }] : [])],
    server: {
      host: "0.0.0.0",
      port: 5173,
      strictPort: true,
      allowedHosts: host ? [host] : [],
      hmr: host ? { protocol: "wss", host, clientPort: 443 } : undefined,
      proxy: { "/api": "http://127.0.0.1:8000" },
    },
  };
});
