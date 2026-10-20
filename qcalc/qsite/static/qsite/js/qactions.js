// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

/* qCalc card/form actions */

(function() {
    const TOK_FORM_PREFIX = 'form-';
    const TOK_EXTRA_PREFIX = 'extra_';
    const TOK_CALCULATE_PREFIX = 'calculate_';

    function updateExtra(cid, dict) {
        var extraFieldId = TOK_EXTRA_PREFIX + cid;
        var extraCurVal = $('#' + extraFieldId).val();
        if (extraCurVal == null) {
            extraCurVal = '{}';
        }
        var oriObj = JSON.parse(extraCurVal);

        if (dict == null) {
            dict = '{}';
        }
        var newObj = dict;

        var extraNewVal = JSON.stringify(Object.assign(oriObj, newObj));
        $('#' + extraFieldId).val(extraNewVal);
    }

    function clearExtraCmd(cid) {
        var extraField = document.getElementById(TOK_EXTRA_PREFIX + cid);
        if (!extraField) {
            return;
        }
        var obj = {};
        try {
            obj = JSON.parse(extraField.value || '{}');
        } catch (_err) {
            extraField.value = '{}';
            return;
        }
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) {
            extraField.value = '{}';
            return;
        }
        if (Object.prototype.hasOwnProperty.call(obj, 'cmd')) {
            delete obj.cmd;
            extraField.value = JSON.stringify(obj);
        }
    }

    function calClick(cid) {
        var calcBtnId = TOK_CALCULATE_PREFIX + cid;
        $('#' + calcBtnId).trigger('click');
    }

    function qcalc_FullFormSubmit(cid) {
        var form = document.getElementById(TOK_FORM_PREFIX + cid);
        if (!form) {
            return;
        }
        form.setAttribute('hx-vals', '{"qcalc_structural_cmd": "1"}');
        form.setAttribute('hx-target', 'this');
        form.setAttribute('hx-swap', 'innerHTML');
        $('#' + TOK_CALCULATE_PREFIX + cid).trigger('click');
    }

    function setRequestPreferences(cid, preferences, structural) {
        updateExtra(cid, preferences);
        if (structural) {
            qcalc_FullFormSubmit(cid);
        }
    }

    function calWithCmd(cid, fname, cmd) { // cmd='save_input', 'save_io', 'save_var', 'create_var'
        updateExtra(cid, { cmd: cmd });
        calClick(cid);
    }

    async function saveInputToFile(cid, fname) {
        var form = document.getElementById(TOK_FORM_PREFIX + cid);
        if (!form) {
            return;
        }

        var downloadName = fname + '.json';
        var fileHandle = null;
        if (window.isSecureContext && typeof window.showSaveFilePicker === 'function') {
            try {
                fileHandle = await window.showSaveFilePicker({
                    suggestedName: downloadName,
                    types: [{
                        description: 'JSON files',
                        accept: { 'application/json': ['.json'] }
                    }]
                });
            } catch (err) {
                if (err && err.name === 'AbortError') {
                    return;
                }
                fileHandle = null;
            }
        }

        var extraField = document.getElementById(TOK_EXTRA_PREFIX + cid);
        var originalExtra = extraField ? (extraField.value || '{}') : null;

        if (extraField) {
            var payload = {};
            try {
                payload = JSON.parse(originalExtra || '{}');
            } catch (_err) {
                payload = {};
            }
            payload.cmd = 'save_io';
            extraField.value = JSON.stringify(payload);
        }

        try {
            var postData = new FormData(form);
            var csrftoken = form.querySelector('[name=csrfmiddlewaretoken]');
            var response = await fetch('/calc/run/' + encodeURIComponent(fname) + '/?part=2', {
                method: 'POST',
                body: postData,
                headers: csrftoken ? { 'X-CSRFToken': csrftoken.value } : {}
            });
            if (!response.ok) {
                throw new Error('Save request failed with status ' + response.status);
            }

            var data = await response.json();
            var jsonText = JSON.stringify(data, null, 2);
            if (fileHandle) {
                var writable = await fileHandle.createWritable();
                await writable.write(jsonText);
                await writable.close();
            } else {
                var blob = new Blob([jsonText], { type: 'application/json;charset=utf-8' });
                saveAs(blob, downloadName);
            }
        } catch (_err) {
            alert('Unable to save input right now. Please try again.');
        } finally {
            if (extraField) {
                extraField.value = originalExtra == null ? '{}' : originalExtra;
                clearExtraCmd(cid);
            }
        }
    }

    function saveInput(fname) { // cmd='save_input', 'save_io', 'save_var', 'create_var'
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/calc/save/');
        xhr.responseType = 'blob';
        var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
        xhr.onload = function() {
            saveAs(xhr.response, fname + '.json'); //FileSaver.min.js
        };
        xhr.send();
    }

    function bindAfterRequestCleanup() {
        document.addEventListener('htmx:afterRequest', function(event) {
            var detail = event.detail || {};
            var elt = detail.elt || event.target;
            var form = elt && elt.tagName === 'FORM'
                ? elt
                : (elt && elt.closest ? elt.closest('form') : null);
            if (!form || !form.id || !form.id.startsWith(TOK_FORM_PREFIX)) {
                return;
            }

            var cid = form.id.replace(TOK_FORM_PREFIX, '');
            clearExtraCmd(cid);
        });
    }

    bindAfterRequestCleanup();

    window.QCalcActions = {
        updateExtra: updateExtra,
        clearExtraCmd: clearExtraCmd,
        calClick: calClick,
        qcalc_FullFormSubmit: qcalc_FullFormSubmit,
        setRequestPreferences: setRequestPreferences,
        calWithCmd: calWithCmd,
        saveInputToFile: saveInputToFile,
        saveInput: saveInput,
    };
})();
