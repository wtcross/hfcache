import * as matchers from "@testing-library/jest-dom/matchers";
import type { TestingLibraryMatchers } from "@testing-library/jest-dom/matchers";
import { cleanup } from "@testing-library/react";
import { afterEach, expect } from "vitest";

// Vitest 5 uses Matchers<R,T>; jest-dom's v7 legacy Assertion augmentation is incompatible.
declare module "vitest" {
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type -- Module augmentation must be an interface.
    interface Matchers<R, T> extends TestingLibraryMatchers<T, R> {}
}
expect.extend(matchers);

afterEach(() => {
    cleanup();
    document.head.querySelector('meta[name="hfcache-ui-base"]')?.remove();
    document.getElementById("root")?.remove();
    window.history.replaceState(null, "", "/ui/");
});
