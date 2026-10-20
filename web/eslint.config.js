import js from "@eslint/js";
import tseslint from "typescript-eslint";
import hooks from "eslint-plugin-react-hooks";
import refresh from "eslint-plugin-react-refresh";

export default tseslint.config(
    {
        ignores: [
            "node_modules/**",
            "dist/**",
            "coverage/**",
            ".cache/**",
            ".artifacts/**",
            "dependencies/**",
            "test/strict-fixtures/**",
        ],
    },
    { ...js.configs.recommended, files: ["*.js"] },
    {
        files: ["**/*.ts", "**/*.tsx"],
        extends: [...tseslint.configs.strictTypeChecked],
        languageOptions: {
            parserOptions: {
                project: ["./tsconfig.json", "./tsconfig.node.json"],
                tsconfigRootDir: import.meta.dirname,
            },
        },
        plugins: { "react-hooks": hooks, "react-refresh": refresh },
        rules: {
            ...hooks.configs.recommended.rules,
            "@typescript-eslint/no-explicit-any": "error",
            "@typescript-eslint/switch-exhaustiveness-check": "error",
            "@typescript-eslint/no-unsafe-type-assertion": "error",
            "react-refresh/only-export-components": [
                "error",
                { allowConstantExport: true },
            ],
            "no-restricted-syntax": [
                "error",
                {
                    selector:
                        'JSXAttribute[name.name="dangerouslySetInnerHTML"]',
                    message: "Render inert React content (AD-15).",
                },
            ],
        },
    },
);
