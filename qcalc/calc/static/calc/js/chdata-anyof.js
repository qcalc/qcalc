// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_AnyofBootstrapped) {
        return;
    }
    window.__qcalc_AnyofBootstrapped = true;

    function clearFieldValue(fieldId) {
        var fieldElem = document.getElementById(fieldId);
        if (fieldElem) {
            fieldElem.value = "";
        }

        var partItems = document.querySelectorAll('[id^="' + fieldId + '"][id$="_part"]');
        for (var k = 0; k < partItems.length; k++) {
            partItems[k].value = "";
        }
    }

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
                return;
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
        var idPrefix = "id_" + cid + "_";

        for (var i = 0; i < groupFields.length; i++) {
            var baseFieldId = idPrefix + groupFields[i];
            bindAnyofField(groupId, groupFields, idPrefix, i, baseFieldId);

            var partItems = document.querySelectorAll('[id^="' + baseFieldId + '"][id$="_part"]');
            for (var k = 0; k < partItems.length; k++) {
                bindAnyofField(groupId, groupFields, idPrefix, i, partItems[k].id);
            }
        }

        for (var m = 0; m < groupFields.length; m++) {
            var triggerElem = document.getElementById(idPrefix + groupFields[m]);
            if (triggerElem) {
                triggerElem.dispatchEvent(new Event("change"));
            }
        }
    }

    function initAnyofByCid(cid) {
        var scriptId = cid + "_script_data_anyof";
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
            .find('script[type="application/json"][id$="_script_data_anyof"]')
            .add($root.filter('script[type="application/json"][id$="_script_data_anyof"]'));

        $scripts.each(function() {
            var scriptId = this.id || "";
            var cid = scriptId.replace(/_script_data_anyof$/, "");
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
