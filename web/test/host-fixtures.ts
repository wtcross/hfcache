/** Original Python model golden; this fixture never runs in the shipped UI. */
import original from "../../tests/fixtures/schemas/host-status.json";
import { decodeHostStatus } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { readWire } from "./read-fixtures";

export function hostStatusFixture() {
    return decodeHostStatus(parseWireJson(JSON.stringify(original)));
}
export function hostStatusWire(payload: unknown = original) {
    return {
        ...readWire("host status", payload),
        archive_id: original.binding.archive_id,
    };
}
