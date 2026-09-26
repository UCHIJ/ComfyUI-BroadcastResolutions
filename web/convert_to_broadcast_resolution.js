import { app } from "../../scripts/app.js";

// Single source of truth: this file loads the same broadcast_profiles.json
// that convert_to_broadcast_resolution.py loads, so the two can no longer
// silently drift apart (which is how the earlier double-space/single-space
// label mismatch happened).
let _profileDataPromise = null;
function loadProfileData() {
    if (!_profileDataPromise) {
        _profileDataPromise = fetch(new URL("./broadcast_profiles.json", import.meta.url))
            .then((r) => r.json());
    }
    return _profileDataPromise;
}

function roundEven(v) {
    let r = Math.round(v);
    if (r % 2 !== 0) r += 1;
    return r;
}

function snapToMultiple(v, multiple) {
    // Always rounds UP, never down — matches the Python side exactly.
    if (!multiple || multiple <= 1) return v;
    return Math.ceil(v / multiple) * multiple;
}

function computeDims(resolution, aspectKey, data) {
    const [nativeW, nativeH] = data.resolutions[resolution] || [1920, 1080];
    const [rw, rh] = data.aspect_ratios[aspectKey] || [16, 9];
    if (rw >= rh) {
        const height = nativeH;
        const width = roundEven(height * (rw / rh));
        return [width, height];
    } else {
        const width = nativeH;
        const height = roundEven(width * (rh / rw));
        return [width, height];
    }
}

// Resolves the node's effective target size, honoring a cinema_delivery
// override when one is selected. Returns null if the convert node or its
// widgets aren't available yet.
function resolveConvertTarget(convertNode, data) {
    if (!convertNode) return null;
    const resW = convertNode.widgets?.find(w => w.name === "resolution");
    const aspW = convertNode.widgets?.find(w => w.name === "aspect_ratio");
    const cinW = convertNode.widgets?.find(w => w.name === "cinema_delivery");
    if (!resW || !aspW) return null;

    const cinemaDims = cinW ? data.cinema_delivery[cinW.value] : null;
    if (cinemaDims) return cinemaDims;
    return computeDims(resW.value, aspW.value, data);
}

app.registerExtension({
    name: "UCHIJ.BroadcastSuite",
    async nodeCreated(node) {
        const data = await loadProfileData();

        // =================================================================
        // 1. CONFORM VIDEO TO RESOLUTION (Output Preview — true broadcast target)
        // =================================================================
        if (node.comfyClass === "ConformVideoToResolution") {
            node.drawBadges = function () {};

            const outputWidget = node.addWidget("text", "output_preview", "---", () => {}, {
                serialize: false,
            });
            if (outputWidget.inputEl) {
                outputWidget.inputEl.readOnly = true;
                outputWidget.inputEl.style.opacity = "0.85";
                outputWidget.inputEl.style.textAlign = "center";
            }

            const pIdx = node.widgets.indexOf(outputWidget);
            if (pIdx > 0) {
                node.widgets.splice(pIdx, 1);
                node.widgets.unshift(outputWidget);
            }

            const updateOutputPreview = () => {
                const convertNode = app.graph?.findNodesByType("ConvertToBroadcastResolution")?.[0];
                const target = resolveConvertTarget(convertNode, data);
                outputWidget.value = target ? `${target[0]}\u00d7${target[1]}` : "1920\u00d71080";
                node.setDirtyCanvas(true, true);
            };

            node.onExecutionStart = updateOutputPreview;
            setTimeout(updateOutputPreview, 100);
            return;
        }

        // =================================================================
        // 2. CONVERT TO BROADCAST RESOLUTION (Input Preview — model-facing size)
        // =================================================================
        if (node.comfyClass !== "ConvertToBroadcastResolution") return;

        node.drawBadges = function () {};

        const resolutionWidget = node.widgets.find(w => w.name === "resolution");
        const aspectWidget = node.widgets.find(w => w.name === "aspect_ratio");
        const cinemaWidget = node.widgets.find(w => w.name === "cinema_delivery");
        const multipleWidget = node.widgets.find(w => w.name === "multiple");
        if (!resolutionWidget || !aspectWidget) return;

        const inputWidget = node.addWidget("text", "input_preview", "", () => {}, {
            serialize: false,
        });
        if (inputWidget.inputEl) {
            inputWidget.inputEl.readOnly = true;
            inputWidget.inputEl.style.opacity = "0.85";
            inputWidget.inputEl.style.textAlign = "center";
        }

        const setLadderWidgetsEnabled = (enabled) => {
            // Dimmed (not hidden) when cinema_delivery is overriding them,
            // so it's visually clear they're not currently in effect.
            resolutionWidget.disabled = !enabled;
            aspectWidget.disabled = !enabled;
            if (resolutionWidget.inputEl) resolutionWidget.inputEl.style.opacity = enabled ? "1" : "0.5";
            if (aspectWidget.inputEl) aspectWidget.inputEl.style.opacity = enabled ? "1" : "0.5";
        };

        const update = () => {
            const cinemaDims = cinemaWidget ? data.cinema_delivery[cinemaWidget.value] : null;
            setLadderWidgetsEnabled(!cinemaDims);

            const [targetW, targetH] = cinemaDims || computeDims(resolutionWidget.value, aspectWidget.value, data);
            const mult = multipleWidget ? multipleWidget.value : 0;
            const snapW = snapToMultiple(targetW, mult);
            const snapH = snapToMultiple(targetH, mult);

            // Input node only ever shows the model-facing (snapped) size.
            // The true broadcast target is the Conform node's concern, not
            // this one's — this node has no idea if a Conform node even
            // exists downstream.
            inputWidget.value = `${snapW}\u00d7${snapH}`;

            node.setDirtyCanvas(true, true);

            // Push the TRUE (unsnapped) broadcast target to any Conform
            // node(s) on the canvas in real time, the instant anything here
            // changes — this is the live "wireless sync" the whole feature
            // is built around, not something that waits for execution.
            const conformNodes = app.graph?.findNodesByType("ConformVideoToResolution") || [];
            for (const cNode of conformNodes) {
                const outputWidget = cNode.widgets?.find(w => w.name === "output_preview");
                if (outputWidget) {
                    outputWidget.value = `${targetW}\u00d7${targetH}`;
                    cNode.setDirtyCanvas(true, true);
                }
            }
        };

        const wrapCallback = (w) => {
            if (!w) return;
            const orig = w.callback;
            w.callback = function (...args) {
                const ret = orig?.apply(this, args);
                update();
                return ret;
            };
        };
        wrapCallback(resolutionWidget);
        wrapCallback(aspectWidget);
        wrapCallback(cinemaWidget);
        wrapCallback(multipleWidget);

        update();
    },
});