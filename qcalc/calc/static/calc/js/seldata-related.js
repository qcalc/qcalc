// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_RelatedBootstrapped) {
        return;
    }
    window.__qcalc_RelatedBootstrapped = true;

    function elemAt(relFields, idPrefix, i) {
        return document.getElementById(idPrefix + relFields[i]);
    }

    function setEnabledState(relFields, idPrefix, activeIndex) {
        for (let j = 0; j < relFields.length; j++) {
            const select = elemAt(relFields, idPrefix, j);
            if (!select) {
                continue;
            }
            select.disabled = (j > (activeIndex + 1));
            select.style.cursor = select.disabled ? "auto" : "pointer";
        }
    }

    function resolveRelatedData(relatedData, relFields, idPrefix, i, targetValue) {
        if (i === 0) {
            return relatedData[targetValue];
        }
        if (i === 1) {
            const elem0 = elemAt(relFields, idPrefix, 0);
            return elem0 ? relatedData[elem0.value]?.[targetValue] : undefined;
        }
        if (i === 2) {
            const elem0 = elemAt(relFields, idPrefix, 0);
            const elem1 = elemAt(relFields, idPrefix, 1);
            return elem0 && elem1 ? relatedData[elem0.value]?.[elem1.value]?.[targetValue] : undefined;
        }
        return undefined;
    }

    function bindRelatedEvent(i, relFields, relatedData, idPrefix) {
        const selected = elemAt(relFields, idPrefix, i);
        if (!selected) {
            return;
        }
        if (selected.dataset.qcalc_RelatedBound === "1") {
            return;
        }

        selected.addEventListener("change", function(e) {
            setEnabledState(relFields, idPrefix, i);
            const rData = resolveRelatedData(relatedData, relFields, idPrefix, i, e.target.value);
            const nextSelect = elemAt(relFields, idPrefix, i + 1);
            if (!nextSelect) {
                return;
            }
            nextSelect.options.length = 0;
            nextSelect.options[0] = new Option("(Select)", "");
            if (!rData) {
                return;
            }

            if (i === relFields.length - 2 && Array.isArray(rData)) {
                for (let k = 0; k < rData.length; k++) {
                    nextSelect.options[nextSelect.options.length] = new Option(rData[k], rData[k]);
                }
            } else {
                for (const keyr in rData) {
                    nextSelect.options[nextSelect.options.length] = new Option(keyr, keyr);
                }
            }
        });

        selected.dataset.qcalc_RelatedBound = "1";
    }

    function initRelatedGroup(groupValue, cid) {
        const relFields = Object.keys(groupValue.fields || {});
        const initialData = Object.values(groupValue.fields || {});
        const relatedData = groupValue.relation || {};
        const idPrefix = "id_" + cid + "_";

        if (relFields.length === 0) {
            return;
        }

        setEnabledState(relFields, idPrefix, 0);

        const firstSelect = elemAt(relFields, idPrefix, 0);
        if (!firstSelect) {
            return;
        }
        firstSelect.options.length = 0;
        firstSelect.options[0] = new Option("(Select)", "");
        for (const keyr in relatedData) {
            firstSelect.options[firstSelect.options.length] = new Option(keyr, keyr);
        }

        for (let i = 0; i < relFields.length - 1; i++) {
            bindRelatedEvent(i, relFields, relatedData, idPrefix);
        }

        for (let i = 0; i < relFields.length; i++) {
            const select = elemAt(relFields, idPrefix, i);
            if (!select) {
                continue;
            }
            select.value = initialData[i];
            select.dispatchEvent(new Event("change"));
        }
    }

    function initRelatedByCid(cid) {
        const scriptId = cid + "_script_data_related";
        const scriptElem = document.getElementById(scriptId);
        if (!scriptElem) {
            return;
        }

        let relatedfldObj = {};
        try {
            relatedfldObj = JSON.parse(scriptElem.textContent || "{}");
        } catch (_e) {
            return;
        }

        Object.entries(relatedfldObj).forEach(function(entry) {
            const value = entry[1];
            initRelatedGroup(value, cid);
        });
    }

    function initRelatedInScope(rootElem) {
        const $root = rootElem ? $(rootElem) : $(document);
        const $scripts = $root
            .find('script[type="application/json"][id$="_script_data_related"]')
            .add($root.filter('script[type="application/json"][id$="_script_data_related"]'));

        $scripts.each(function() {
            const scriptId = this.id || "";
            const cid = scriptId.replace(/_script_data_related$/, "");
            if (cid) {
                initRelatedByCid(cid);
            }
        });
    }

    window.qcalc_InitRelated = function(formOrElemOrCid) {
        if (typeof formOrElemOrCid === "string") {
            initRelatedByCid(formOrElemOrCid);
            return;
        }
        initRelatedInScope(formOrElemOrCid || document);
    };

    $(document).ready(function() {
        initRelatedInScope(document);
    });

    document.body.addEventListener("htmx:afterSwap", function(evt) {
        const target = evt && evt.detail ? evt.detail.target : null;
        initRelatedInScope(target || document);
    });
})();

