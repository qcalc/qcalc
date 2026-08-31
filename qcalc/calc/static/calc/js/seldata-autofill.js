// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_AutofillBootstrapped) {
        return;
    }
    window.__qcalc_AutofillBootstrapped = true;

    function applyAutofillValues(autofillFields, selectedData, idPrefix) {
        for (var i = 0; i < autofillFields.length; i++) {
            var targetElem = document.getElementById(idPrefix + autofillFields[i]);
            if (!targetElem) {
                continue;
            }

            var newValue = selectedData ? selectedData[i] : null;
            if (newValue != null) {
                targetElem.value = newValue;
                targetElem.readOnly = true;
            } else {
                targetElem.readOnly = false;
            }
        }
    }

    function bindAutofillEvent(groupId, selectedId, autofillFields, autofillData, idPrefix) {
        var selectedElem = document.getElementById(selectedId);
        if (!selectedElem) {
            return;
        }

        var token = "|" + groupId + "|";
        var boundGroups = selectedElem.dataset.qcalc_AutofillBound || "";
        if (boundGroups.indexOf(token) !== -1) {
            return;
        }

        selectedElem.addEventListener("change", function(e) {
            var sourceElem = e && e.target ? e.target : selectedElem;
            var selectedVal = sourceElem.value;
            var selectedData = autofillData ? autofillData[selectedVal] : null;
            applyAutofillValues(autofillFields, selectedData, idPrefix);
        });

        selectedElem.dataset.qcalc_AutofillBound = boundGroups + token;
    }

    function initAutofillByCid(cid) {
        var scriptId = cid + "_script_data_autofill";
        var scriptElem = document.getElementById(scriptId);
        if (!scriptElem) {
            return;
        }

        var autofillObj = {};
        try {
            autofillObj = JSON.parse(scriptElem.textContent || "{}");
        } catch (_e) {
            return;
        }

        var idPrefix = "id_" + cid + "_";

        Object.entries(autofillObj).forEach(function(entry) {
            var key = entry[0];
            var value = entry[1] || {};
            var selectedId = idPrefix + key;
            var autofillFields = value.fields || [];
            // accept 'values' as the preferred key, falling back to legacy 'autofill'
            var autofillData = value.values || value.autofill || {};

            bindAutofillEvent(cid + "::" + key, selectedId, autofillFields, autofillData, idPrefix);
        });

        Object.entries(autofillObj).forEach(function(entry) {
            var key = entry[0];
            var selectedId = idPrefix + key;
            var selectedElem = document.getElementById(selectedId);
            if (selectedElem) {
                selectedElem.dispatchEvent(new Event("change"));
            }
        });
    }

    function initAutofillInScope(rootElem) {
        var $root = rootElem ? $(rootElem) : $(document);
        var $scripts = $root
            .find('script[type="application/json"][id$="_script_data_autofill"]')
            .add($root.filter('script[type="application/json"][id$="_script_data_autofill"]'));

        $scripts.each(function() {
            var scriptId = this.id || "";
            var cid = scriptId.replace(/_script_data_autofill$/, "");
            if (cid) {
                initAutofillByCid(cid);
            }
        });
    }

    window.qcalc_InitAutofill = function(formOrElemOrCid) {
        if (typeof formOrElemOrCid === "string") {
            initAutofillByCid(formOrElemOrCid);
            return;
        }
        initAutofillInScope(formOrElemOrCid || document);
    };

    $(document).ready(function() {
        initAutofillInScope(document);
    });

    document.body.addEventListener("htmx:afterSwap", function(evt) {
        var target = evt && evt.detail ? evt.detail.target : null;
        initAutofillInScope(target || document);
    });
})();
