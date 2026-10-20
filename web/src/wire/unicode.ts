/** Exact Python Unicode16 NFC/full casefold; see dependencies/UNICODE-LICENSE.txt. */
import tables from "./unicode-data.json";
import { codePointLength, WireError } from "./json";

export const PYTHON_UNICODE_VERSION = "16.0.0";
if (
    tables.schema_version !== 1 ||
    tables.unicode_version !== PYTHON_UNICODE_VERSION
)
    throw new WireError("semantic");

const combining = new Map(
    Object.entries(tables.combining).map(([point, order]): [number, number] => [
        Number(point),
        order,
    ]),
);
const decompositions = new Map(
    Object.entries(tables.decompositions).map(
        ([point, parts]): [number, readonly number[]] => [Number(point), parts],
    ),
);
const compositions = new Map(Object.entries(tables.compositions));
const casefold = new Map(
    Object.entries(tables.casefold).map(([point, folded]): [number, string] => [
        Number(point),
        folded,
    ]),
);

/** Shared by a manifest's complete path set, not reset per collision candidate. */
export class UnicodeWork {
    private remaining: number;
    constructor(maximum = 8_000_000) {
        if (
            !Number.isSafeInteger(maximum) ||
            maximum < 1 ||
            maximum > 8_000_000
        )
            throw new WireError("bounds");
        this.remaining = maximum;
    }
    step(): void {
        if (--this.remaining < 0) throw new WireError("bounds");
    }
}

function point(character: string): number {
    const value = character.codePointAt(0);
    if (value === undefined) throw new WireError("semantic");
    return value;
}

// UAX15's algorithmic Hangul decomposition/composition, independent of engine UCD.
const SBASE = 0xac00;
const LBASE = 0x1100;
const VBASE = 0x1161;
const TBASE = 0x11a7;
const LCOUNT = 19;
const VCOUNT = 21;
const TCOUNT = 28;
const NCOUNT = VCOUNT * TCOUNT;
const SCOUNT = LCOUNT * NCOUNT;

function decompose(
    value: number,
    output: number[],
    work: UnicodeWork,
    depth: number,
): void {
    work.step();
    if (depth > 32) throw new WireError("bounds");
    const syllable = value - SBASE;
    if (syllable >= 0 && syllable < SCOUNT) {
        output.push(LBASE + Math.floor(syllable / NCOUNT));
        output.push(VBASE + Math.floor((syllable % NCOUNT) / TCOUNT));
        const tail = syllable % TCOUNT;
        if (tail !== 0) output.push(TBASE + tail);
    } else {
        const parts = decompositions.get(value);
        if (parts === undefined) output.push(value);
        else for (const part of parts) decompose(part, output, work, depth + 1);
    }
}

function compose(first: number, second: number): number | undefined {
    const leading = first - LBASE;
    const vowel = second - VBASE;
    if (leading >= 0 && leading < LCOUNT && vowel >= 0 && vowel < VCOUNT)
        return SBASE + (leading * VCOUNT + vowel) * TCOUNT;
    const syllable = first - SBASE;
    const tail = second - TBASE;
    if (
        syllable >= 0 &&
        syllable < SCOUNT &&
        syllable % TCOUNT === 0 &&
        tail > 0 &&
        tail < TCOUNT
    )
        return first + tail;
    return compositions.get(`${String(first)},${String(second)}`);
}

export function pythonNfc(value: string, work = new UnicodeWork()): string {
    codePointLength(value);
    const decomposed: number[] = [];
    for (const character of value)
        decompose(point(character), decomposed, work, 0);
    // Stable canonical ordering. Path grammar caps each input at1024UTF8 bytes;
    // the shared work budget also bounds adversarial combining runs.
    for (let index = 1; index < decomposed.length; index++) {
        const current = decomposed[index];
        if (current === undefined) throw new WireError("semantic");
        const order = combining.get(current) ?? 0;
        if (order === 0) continue;
        let position = index;
        while (position > 0) {
            work.step();
            const previous = decomposed[position - 1];
            if (previous === undefined) throw new WireError("semantic");
            if ((combining.get(previous) ?? 0) <= order) break;
            decomposed[position] = previous;
            position--;
        }
        decomposed[position] = current;
    }
    const initial = decomposed[0];
    if (initial === undefined) return "";
    const result = [initial];
    let starter = initial;
    let starterPosition = 0;
    let lastClass = combining.get(initial) ?? 0;
    for (let index = 1; index < decomposed.length; index++) {
        work.step();
        const current = decomposed[index];
        if (current === undefined) throw new WireError("semantic");
        const order = combining.get(current) ?? 0;
        const composite = compose(starter, current);
        if (composite !== undefined && (lastClass < order || lastClass === 0)) {
            result[starterPosition] = composite;
            starter = composite;
        } else {
            if (order === 0) {
                starterPosition = result.length;
                starter = current;
            }
            result.push(current);
            lastClass = order;
        }
    }
    return result.map((item) => String.fromCodePoint(item)).join("");
}

export function pythonCasefold(
    value: string,
    work = new UnicodeWork(),
): string {
    const pieces: string[] = [];
    codePointLength(value);
    for (const character of value) {
        work.step();
        pieces.push(casefold.get(point(character)) ?? character);
    }
    return pieces.join("");
}

/** Exact Python str.isprintable, including empty strings and unassigned points. */
export function pythonIsPrintable(value: string): boolean {
    for (const character of value) {
        const current = point(character);
        let lower = 0;
        let upper = tables.nonprintable.length;
        while (lower < upper) {
            const index = Math.floor((lower + upper) / 2);
            const range = tables.nonprintable[index];
            if (
                range === undefined ||
                range[0] === undefined ||
                range[1] === undefined
            )
                throw new WireError("semantic");
            if (current < range[0]) upper = index;
            else if (current > range[1]) lower = index + 1;
            else return false;
        }
    }
    return true;
}

/** Python paths.collision_key: NFC then full casefold, with no final normalization. */
export function pythonCollisionKey(
    value: string,
    work = new UnicodeWork(),
): string {
    return pythonCasefold(pythonNfc(value, work), work);
}
