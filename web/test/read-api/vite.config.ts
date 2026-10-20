import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

export default defineConfig({
    root: fileURLToPath(new URL("./", import.meta.url)),
    plugins: [react()],
    base: "./",
    build: {
        target: ["chrome111", "firefox114", "safari16.4"],
        sourcemap: false,
        assetsInlineLimit: 0,
        emptyOutDir: false,
    },
});
