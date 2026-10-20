import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    test: {
        globals: false,
        clearMocks: true,
        restoreMocks: true,
        retry: 0,
        testTimeout: 10000,
        projects: [
            {
                test: {
                    name: "unit",
                    environment: "node",
                    include: ["test/*.unit.test.ts"],
                },
            },
            {
                test: {
                    name: "component",
                    environment: "jsdom",
                    include: ["test/*.component.test.tsx"],
                    setupFiles: ["test/setup.ts"],
                    environmentOptions: {
                        jsdom: { url: "http://localhost/ui/" },
                    },
                },
            },
        ],
        coverage: {
            provider: "v8",
            include: ["src/**/*.{ts,tsx}"],
            reporter: ["text", "json-summary", "lcov"],
            thresholds: {
                lines: 90,
                statements: 90,
                functions: 90,
                branches: 85,
            },
        },
    },
});
