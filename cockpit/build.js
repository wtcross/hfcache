#!/usr/bin/env node
/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Derived from cockpit-project/starter-kit build.js @ a099cb10, adapted for
 * this repository (docs/cockpit.md §8): pnpm layout awareness for the bundled
 * package listing, no gettext/po pipeline, native esbuild only.
 */

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

import { sassPlugin } from 'esbuild-sass-plugin';

import { cockpitRsyncEsbuildPlugin } from './pkg/lib/cockpit-rsync-plugin.js';
import { cleanPlugin } from './pkg/lib/esbuild-cleanup-plugin.js';
import { cockpitCompressPlugin } from './pkg/lib/esbuild-compress-plugin.js';

const esbuild = (await import('esbuild')).default;

const production = process.env.NODE_ENV === 'production';
// List of directories to use when using import statements
const nodePaths = ['pkg/lib'];
const outdir = 'dist';

// Obtain package name from package.json
const packageJson = JSON.parse(fs.readFileSync('package.json'));

const parser = (await import('argparse')).default.ArgumentParser();
/* eslint-disable max-len */
parser.add_argument('-r', '--rsync', { help: "rsync bundles to ssh target after build", metavar: "HOST" });
parser.add_argument('-w', '--watch', { action: 'store_true', help: "Enable watch mode", default: process.env.ESBUILD_WATCH === "true" });
/* eslint-enable max-len */
const args = parser.parse_args();

if (args.rsync)
    process.env.RSYNC = args.rsync;

function notifyEndPlugin() {
    return {
        name: 'notify-end',
        setup(build) {
            let startTime;

            build.onStart(() => {
                startTime = new Date();
            });

            build.onEnd(() => {
                const endTime = new Date();
                const timeStamp = endTime.toTimeString().split(' ')[0];
                console.log(`${timeStamp}: Build finished in ${endTime - startTime} ms`);
            });
        }
    };
}

// similar to fs.watch(), but recursively watches all subdirectories
function watch_dirs(dir, on_change) {
    const callback = (ev, dir, fname) => {
        // only listen for "change" events, as renames are noisy
        // ignore hidden files
        if (ev !== "change" || fname.startsWith('.')) {
            return;
        }
        on_change(path.join(dir, fname));
    };

    fs.watch(dir, {}, (ev, path) => callback(ev, dir, path));

    // watch all subdirectories in dir
    const d = fs.opendirSync(dir);
    let dirent;

    while ((dirent = d.readSync()) !== null) {
        if (dirent.isDirectory())
            watch_dirs(path.join(dir, dirent.name), on_change);
    }
    d.closeSync();
}

// Bundled package names and versions, from the metafile input paths. Handles
// both the pnpm layout (node_modules/.pnpm/<name>@<version>/node_modules/…,
// which is what esbuild's realpath resolution reports here) and the flat npm
// layout the starter kit reads package-lock.json for.
function bundledPackageVersions(metafile) {
    const found = new Map();
    for (const inputPath of Object.keys(metafile.inputs)) {
        const pnpmMatch = inputPath.match(/node_modules\/\.pnpm\/([^/]+)\//);
        if (pnpmMatch) {
            const spec = pnpmMatch[1];
            const at = spec.lastIndexOf('@');
            if (at > 0) {
                const name = spec.slice(0, at).replaceAll('+', '/');
                const version = spec.slice(at + 1).split('_')[0];
                found.set(name, version);
            }
            continue;
        }
        const npmMatch = inputPath.match(/^node_modules\/(@[^/]+\/[^/]+|[^/]+)\//);
        if (npmMatch && !found.has(npmMatch[1])) {
            try {
                const pkg = JSON.parse(
                    fs.readFileSync(path.join('node_modules', npmMatch[1], 'package.json'), 'utf8'));
                found.set(npmMatch[1], pkg.version);
            } catch {
                console.error(`Warning: Could not find version for ${npmMatch[1]}`);
            }
        }
    }
    return [...found.entries()]
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([name, version]) => `${name} ${version}`);
}

const context = await esbuild.context({
    ...!production ? { sourcemap: "linked" } : {},
    bundle: true,
    entryPoints: ['./src/index.tsx'],
    // Allow external font files which live in ../../static/fonts
    external: ['*.woff', '*.woff2', '*.jpg', '*.svg', '../../assets*'],
    // Move all legal comments to a .LEGAL.txt file
    legalComments: 'external',
    loader: { ".js": "jsx" },
    minify: production,
    nodePaths,
    // TypeScript uses our narrow declaration; runtime uses the pinned helper.
    alias: { superuser: path.resolve('pkg/lib/superuser.js') },
    outdir,
    metafile: true,
    target: ['es2020'],
    plugins: [
        cleanPlugin(),
        // Esbuild will only copy assets that are explicitly imported and used in the code.
        // Copy the other files here.
        {
            name: 'copy-assets',
            setup(build) {
                build.onEnd((output, _outputFiles) => {
                    if (output?.errors.length === 0) {
                        fs.copyFileSync('./src/manifest.json', './dist/manifest.json');
                        fs.copyFileSync('./src/index.html', './dist/index.html');
                    }
                });
            }
        },

        sassPlugin({
            loadPaths: [...nodePaths, 'node_modules'],
            filter: /\.scss/,
            quietDeps: true,
        }),

        ...production ? [cockpitCompressPlugin()] : [],
        cockpitRsyncEsbuildPlugin({ dest: packageJson.name }),
        notifyEndPlugin(),
    ]
});

try {
    const result = await context.rebuild();

    // skip metafile and runtime module calculation in watch mode
    if (!args.watch) {
        fs.writeFileSync('metafile.json', JSON.stringify(result.metafile));
        fs.writeFileSync('runtime-npm-modules.txt', bundledPackageVersions(result.metafile).join('\n') + '\n');
    }
} catch (e) {
    if (!args.watch)
        process.exit(1);
    // ignore errors in watch mode
}

if (args.watch) {
    const on_change = async path => {
        console.log("change detected:", path);
        await context.cancel();

        try {
            await context.rebuild();
        } catch (e) {} // ignore in watch mode
    };

    watch_dirs('src', on_change);

    // wait forever until Control-C
    await new Promise(() => {});
}

context.dispose();
