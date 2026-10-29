# Browser and keyboard use

Use a current Chromium, Firefox or Safari/WebKit browser with verified HTTPS,
JavaScript, Web Crypto and native JSON number-source support. Older engines
that cannot validate numeric input stop with an unsupported-browser explanation;
they do not display rounded archive sizes. Browser-native sign-in and certificate
trust belong to your browser profile. Never dismiss a certificate warning to
reach the interface. See [sign-in and startup](README.md).

The interface uses local system fonts and respects **Reduce motion** in the
operating system or browser. External fonts and README media are not loaded.
Normal browser zoom and text selection remain available. On narrow screens,
**Open navigation** opens the workspace menu; **Close navigation** returns to the
page. Wide tables have a labelled scroll area so their controls remain reachable.
Repository captions and small evidence text use the same readable foreground as
other secondary text; captions still describe the evidence's loaded scope.
Primary repository actions retain a dark background and readable text when
hovered.

## Navigate without a pointer

Use Tab and Shift+Tab to move between controls. The first **Skip to content**
link bypasses the navigation. Focus has a visible outline. Activate buttons with
Enter or Space and links with Enter. A disabled action remains unavailable until
its displayed prerequisites are satisfied; keyboard use grants no extra authority.

Filter choice lists support arrow keys and Home/End. Enter chooses
the active option, Escape closes the list, and Tab leaves it. Repository evidence
tabs use Left/Right arrows and Home/End. Headings, table headers, field labels,
status updates and errors describe the current loaded scope.

Related explanations and controls are grouped under **Selected job effects**
and **Host controls**. The keyboard-focusable **Sanitized README source** group
contains the exact escaped presentation text for the selected publication.

Leaving a dirty configuration or Administration form opens a confirmation dialog.
Tab and Shift+Tab stay within the dialog. Escape or the keep-editing action
returns to the form; the discard action leaves it. Read the review before the
separate Apply/submit confirmation. Validation errors do not submit an effect.

For a large [manifest table](repository-details.md#inspect-files-within-the-read-budget), focus its
scroll area and use Up/Down, Page Up/Down or Home/End. **File number** and **Go to
file** reach an exact row. **Inspect metadata** focuses its complete path and
evidence below the window; **Return to selected file** restores the row control.
Each inspect button announces **Inspect metadata** and its loaded file number;
the row header and selected evidence retain the full path.
The table reports actual row positions even though most rows are not mounted.
Scrolling and inspecting metadata fetch no payload file.

## Work within bounded reads

The [Library](library.md#page-and-bookmark-a-bounded-read) loads explicit pages,
not the entire archive. Filters describe server scope; loaded rows and metadata
coverage remain separate. Select fewer rows or narrow the scope when a read is
too large. A smaller file-table window does not shrink the complete manifest
response or its validation cost. An oversized, unsafe or exhausted response is a
visible refusal, never a shortened successful manifest.
Byte, structural-token and path-validation limits are independent. A manifest
can fit the byte limit and still exceed another bound. A smaller table page does
not make that artifact valid; preserve its exact publication and diagnostic when
asking the operator to investigate.
The HTTP response also includes its envelope and JSON escaping, so its byte
size can exceed the durable manifest file's size, especially for Unicode paths.

The browser shares finite read concurrency and a 32 MiB budget for encoded
retained evidence. That budget is not a JavaScript heap or browser-process memory
ceiling. Large manifests and multiple private views can exhaust it. Leaving a
repository detail releases its owned evidence; a later visit revalidates the
selected publication. Browser memory also includes fonts, accessibility data,
rendering and runtime allocations.

When the tab becomes hidden, original-operation observation pauses. Returning
does not restart polling: choose **Observe original operation** or the matching
original-outcome action deliberately. Backend jobs continue independently. Keep
original handles through interruption, and preserve them before an interface
reload. See [observation and recovery](operations.md#finite-observation).

Saving an imported original handle gives local feedback without moving focus:
a rejected handle is an error alert, while a successful save uses a polite
status announcement. Neither result submits an operation or starts observation;
choose **Observe original operation** explicitly.

Automated accessibility checks cover specific interface states; they do not
establish full accessibility conformance for every browser, assistive technology
or archive. Keyboard and screen-reader workflows require their own checks with
the matching installed interface. If your reader cannot reach a table row, use
its explicit file-number/page controls and preserve the exact
publication when reporting the problem. Do not infer success from missing or
unannounced evidence.
