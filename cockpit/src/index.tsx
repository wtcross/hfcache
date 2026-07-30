/*
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Derived from cockpit-project/starter-kit src/index.tsx @ a099cb10.
 */

import React from 'react';
import { createRoot } from 'react-dom/client';

import "cockpit-dark-theme";

import { Application } from './app';

import "patternfly/patternfly-6-cockpit.scss";
import './app.scss';

document.addEventListener("DOMContentLoaded", () => {
    createRoot(document.getElementById("app")!).render(<Application />);
});
