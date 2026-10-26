// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

// "anyof" groups from a calculator's __info(), e.g. {"1": {"fields": ["x", "y", "z"]}}:
// only one field of a group keeps a value. Entering a value in one field clears the others.
// Fields are not hidden (see showhide for that) and are cleared by setting .value, which fires no change event.
(function() {
    const TOK_ID_PREFIX = "id_";
    const TOK_FIELD_SEP = "_";
    const TOK_SCRIPT_DATA_ANYOF_SUFFIX = "_script_data_anyof";
    const TOK_PART = "_part";

    if (window.__qcalc_AnyofBootstrapped) {
        return;
    }
    window.__qcalc_AnyofBootstrapped = true;

    // Clear a field and its "_part" sub-inputs (composite fields such as quantity keep each part in its own input).
    function clearFieldValue(fieldId) {
        var fieldElem = document.getElementById(fieldId);
        if (fieldElem) {
            fieldElem.value = "";
        }

        var partItems = document.querySelectorAll('[id^="' + fieldId + '"][id$="' + TOK_PART + '"]');
        for (var k = 0; k < partItems.length; k++) {
            partItems[k].value = "";
        }
    }

    // i is the position of this field in the group, so its siblings are the other indexes.
    // The "bound" token stops the listener being added twice when the form is re-initialised after an htmx swap.
    function bindAnyofField(groupId, groupFields, idPrefix, i, fieldId) {
        var fieldElem = document.getElementById(fieldId);
        if (!fieldElem) {
            return;
        }

        var token = "|" + groupId + "::" + i + "|";
        var boundGroups = fieldElem.dataset.qcalc_AnyofBound || "";
        if (boundGroups.indexOf(token) !== -1) {
            return;
        }

        fieldElem.addEventListener("change", function() {
            var editedVal = fieldElem.value;
            if (!editedVal) {
                return;  // emptying a field leaves the others as they are
            }

            for (var j = 0; j < groupFields.length; j++) {
                if (j !== i) {
                    clearFieldValue(idPrefix + groupFields[j]);
                }
            }
        });

        fieldElem.dataset.qcalc_AnyofBound = boundGroups + token;
    }

    function initAnyofGroup(groupId, groupValue, cid) {
        var groupFields = (groupValue && groupValue.fields) ? groupValue.fields : [];
        var idPrefix = TOK_ID_PREFIX + cid + TOK_FIELD_SEP;

        for (var i = 0; i < groupFields.length; i++) {
            var baseFieldId = idPrefix + groupFields[i];
            bindAnyofField(groupId, groupFields, idPrefix, i, baseFieldId);

            var partItems = document.querySelectorAll('[id^="' + baseFieldId + '"][id$="' + TOK_PART + '"]');
            for (var k = 0; k < partItems.length; k++) {
                bindAnyofField(groupId, groupFields, idPrefix, i, partItems[k].id);
            }
        }

        // Fire a change on each base field so a pre-filled field clears its siblings when the form opens.
        // Where several fields are pre-filled, the first one in the group wins.
        for (var m = 0; m < groupFields.length; m++) {
            var triggerElem = document.getElementById(idPrefix + groupFields[m]);
            if (triggerElem) {
                triggerElem.dispatchEvent(new Event("change"));
            }
        }
    }

    function initAnyofByCid(cid) {
        var scriptId = cid + TOK_SCRIPT_DATA_ANYOF_SUFFIX;
        var scriptElem = document.getElementById(scriptId);
        if (!scriptElem) {
            return;
        }

        var anyofObj = {};
        try {
            anyofObj = JSON.parse(scriptElem.textContent || "{}");
        } catch (_e) {
            return;
        }

        Object.entries(anyofObj).forEach(function(entry) {
            var key = entry[0];
            var value = entry[1];
            initAnyofGroup(cid + "::" + key, value, cid);
        });
    }

    function initAnyofInScope(rootElem) {
        var $root = rootElem ? $(rootElem) : $(document);
        var $scripts = $root
            .find('script[type="application/json"][id$="' + TOK_SCRIPT_DATA_ANYOF_SUFFIX + '"]')
            .add($root.filter('script[type="application/json"][id$="' + TOK_SCRIPT_DATA_ANYOF_SUFFIX + '"]'));

        $scripts.each(function() {
            var scriptId = this.id || "";
            var cid = scriptId.endsWith(TOK_SCRIPT_DATA_ANYOF_SUFFIX)
                ? scriptId.slice(0, -TOK_SCRIPT_DATA_ANYOF_SUFFIX.length)
                : "";
            if (cid) {
                initAnyofByCid(cid);
            }
        });
    }

    window.qcalc_InitAnyof = function(formOrElemOrCid) {
        if (typeof formOrElemOrCid === "string") {
            initAnyofByCid(formOrElemOrCid);
            return;
        }
        initAnyofInScope(formOrElemOrCid || document);
    };

    $(document).ready(function() {
        initAnyofInScope(document);
    });

    document.body.addEventListener("htmx:afterSwap", function(evt) {
        var target = evt && evt.detail ? evt.detail.target : null;
        initAnyofInScope(target || document);
    });
})();
