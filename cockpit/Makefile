# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Cockpit plugin build (docs/cockpit.md §8). Derived from
# cockpit-project/starter-kit @ a099cb10, adapted to pnpm and to this
# repository's layout: no RPM/tarball targets, no gettext pipeline, no
# test-VM machinery — packaging is `install`, and the browser test framework
# is a stated version-1 non-goal (docs/cockpit.md §9).

PACKAGE_NAME := hfcache
PREFIX ?= /usr
DESTDIR ?=

# pnpm lives in the operator's PNPM_HOME and is only on login-shell PATH;
# resolve it the way scripts/check.sh does (docs/cockpit.md §8).
PNPM ?= $(shell command -v pnpm 2>/dev/null || echo $${PNPM_HOME:-$$HOME/.local/share/pnpm}/bin/pnpm)

# Lifecycle scripts and build.js need `node` beside pnpm; a non-login shell
# does not carry PNPM_HOME on PATH, so give every recipe the resolved pnpm's
# own directory.
export PATH := $(dir $(PNPM)):$(PATH)

# Common build files from the Cockpit repository (esbuild plugins, cockpit.js
# and its typings, PatternFly SCSS glue). Same pin as starter-kit @ a099cb10
# ("364 + 95 commits"), matching the cockpit 364 this deployment runs. There
# is no API stability guarantee for pkg/lib; move the pin deliberately.
COCKPIT_REPO_URL = https://github.com/cockpit-project/cockpit.git
COCKPIT_REPO_COMMIT = 47108e2f8ecac3cd71fb3372193dd0f9c0fba7b3
COCKPIT_REPO_STAMP = pkg/lib/cockpit.js

NODE_MODULES_STAMP = node_modules/.pnpm-install-stamp
DIST_STAMP = dist/manifest.json

all: $(DIST_STAMP)

# Fetch pkg/lib into a throwaway repository rather than this one, so the
# cockpit objects never enter this repository's object store.
$(COCKPIT_REPO_STAMP): Makefile
	rm -rf .cockpit-repo
	git init -q .cockpit-repo
	git -C .cockpit-repo fetch -q --no-tags --depth=1 $(COCKPIT_REPO_URL) $(COCKPIT_REPO_COMMIT)
	git -C .cockpit-repo archive $(COCKPIT_REPO_COMMIT) -- pkg/lib | tar x
	rm -rf .cockpit-repo
	touch $(COCKPIT_REPO_STAMP)

$(NODE_MODULES_STAMP): package.json pnpm-lock.yaml
	$(PNPM) install --frozen-lockfile
	touch $(NODE_MODULES_STAMP)

$(DIST_STAMP): $(NODE_MODULES_STAMP) $(COCKPIT_REPO_STAMP) $(shell find src -type f 2>/dev/null) build.js package.json
	NODE_ENV=$(NODE_ENV) $(PNPM) run build

watch: $(NODE_MODULES_STAMP) $(COCKPIT_REPO_STAMP)
	$(PNPM) run watch

lint: $(NODE_MODULES_STAMP) $(COCKPIT_REPO_STAMP)
	$(PNPM) run eslint
	$(PNPM) run stylelint
	$(PNPM) run typecheck

test: $(NODE_MODULES_STAMP)
	$(PNPM) run test

# The plugin gate scripts/check.sh invokes (docs/cockpit.md §8): frozen
# install, lint, unit tests, and a fresh production build.
check: lint test
	rm -f $(DIST_STAMP)
	$(MAKE) NODE_ENV=production $(DIST_STAMP)

install: $(DIST_STAMP)
	mkdir -p $(DESTDIR)$(PREFIX)/share/cockpit/$(PACKAGE_NAME)
	cp -r dist/* $(DESTDIR)$(PREFIX)/share/cockpit/$(PACKAGE_NAME)

devel-install: $(DIST_STAMP)
	mkdir -p ~/.local/share/cockpit
	ln -snf $(CURDIR)/dist ~/.local/share/cockpit/$(PACKAGE_NAME)

devel-uninstall:
	rm -f ~/.local/share/cockpit/$(PACKAGE_NAME)

clean:
	rm -rf dist
	rm -f metafile.json runtime-npm-modules.txt

distclean: clean
	rm -rf node_modules pkg .cockpit-repo

.PHONY: all watch lint test check install devel-install devel-uninstall clean distclean
