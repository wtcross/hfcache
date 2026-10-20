import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    base: "./",
    build: {
        target: ["chrome111", "firefox114", "safari16.4"],
        assetsInlineLimit: 0,
        sourcemap: false,
        emptyOutDir: true,
    },
});
