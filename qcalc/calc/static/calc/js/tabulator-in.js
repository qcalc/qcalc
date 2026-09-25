// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_TabulatorInBootstrapped) {
        return;
    }
    window.__qcalc_TabulatorInBootstrapped = true;

    const tableDf = {};
    const colNames = {};
    const colTitles = {};
    const TOK_ROW = "_row";
    const TOK_COL = "_col";
    const TOK_TABLE_UPDATE = "_table_update";
    const TOK_TABLE_RESIZE = "_table_resize";
    const TOK_TABLE_ED = "_table_ed";
    const TOK_ID_PREFIX = "id_";
    const TOK_FORM_PREFIX = "form-";
    const TOK_EXTRA_PREFIX = "extra_";

    function tableDataFieldId(tableId) {
        return TOK_ID_PREFIX + tableId;
    }

    function tableControlId(tableId, suffixToken) {
        return tableDataFieldId(tableId) + suffixToken;
    }

    // Parse one CSV line with quoted-field handling (double quotes escaped as "").
    function parseCsvLine(line) {
        const out = [];
        let cur = "";
        let inQuotes = false;
        for (let i = 0; i < line.length; i++) {
            const ch = line[i];
            if (ch === '"') {
                if (inQuotes && line[i + 1] === '"') {
                    cur += '"';
                    i += 1;
                } else {
                    inQuotes = !inQuotes;
                }
            } else if (ch === ',' && !inQuotes) {
                out.push(cur);
                cur = "";
            } else {
                cur += ch;
            }
        }
        out.push(cur);
        return out;
    }

    // Ensure unique field keys even when uploaded header titles are duplicated.
    function toUniqueFields(headers) {
        const seen = {};
        return headers.map(function(h, idx) {
            const base = (String(h || "").trim() || ("col_" + String(idx + 1)));
            if (seen[base] == null) {
                seen[base] = 1;
                return base;
            }
            const n = ++seen[base];
            return base + "_" + String(n);
        });
    }

    // Deterministic CSV upload path: first non-empty line is header, remaining lines are rows.
    function importCsvWithHeaders(table) {
        const picker = document.createElement("input");
        picker.type = "file";
        picker.accept = ".csv,.txt,text/csv";
        picker.style.display = "none";
        document.body.appendChild(picker);

        picker.addEventListener("change", function() {
            const file = picker.files && picker.files[0] ? picker.files[0] : null;
            if (!file) {
                document.body.removeChild(picker);
                return;
            }

            const reader = new FileReader();
            reader.onload = function() {
                try {
                    const text = String(reader.result || "").replace(/^\uFEFF/, "");
                    const lines = text.split(/\r?\n/).filter(function(l) {
                        return l.trim() !== "";
                    });
                    if (lines.length === 0) {
                        document.body.removeChild(picker);
                        return;
                    }

                    const headerTitles = parseCsvLine(lines[0]).map(function(h, idx) {
                        const t = String(h == null ? "" : h).trim();
                        return t || ("col_" + String(idx + 1));
                    });
                    const fields = toUniqueFields(headerTitles);

                    const columns = fields.map(function(field, idx) {
                        return {
                            title: headerTitles[idx],
                            field: field,
                            headerSort: false,
                            editor: true,
                            editableTitle: true,
                        };
                    });

                    const rows = lines.slice(1).map(function(line) {
                        const vals = parseCsvLine(line);
                        const row = {};
                        for (let i = 0; i < fields.length; i++) {
                            row[fields[i]] = (vals[i] != null ? vals[i] : "");
                        }
                        return row;
                    });

                    table.setColumns(columns);
                    const setDataResult = table.setData(rows);
                    if (setDataResult && typeof setDataResult.then === "function") {
                        setDataResult.then(function() {
                            afterTableImport(table);
                        });
                    } else {
                        afterTableImport(table);
                    }
                } finally {
                    document.body.removeChild(picker);
                }
            };
            reader.readAsText(file);
        });

        picker.click();
    }

    // After any import, rebuild editable columns from current row keys.
    function syncColumnsFromUploadedData(table) {
        const rows = table.getData();
        if (!rows || rows.length === 0) {
            return;
        }
        const keys = Object.keys(rows[0]).filter(function(key) {
            return key !== "id";
        });
        if (keys.length === 0) {
            return;
        }

        const columns = keys.map(function(key) {
            return {
                title: key,
                field: key,
                headerSort: false,
                editor: true,
                editableTitle: true,
            };
        });
        table.setColumns(columns);
    }

    // Keep hidden JSON payload and button state in sync after import.
    function afterTableImport(table) {
        syncColumnsFromUploadedData(table);
        const tableId = table && table.element ? table.element.id : "";
        if (tableId) {
            setUpdateButtonEnabled(tableId, true);
        }
        pickData(table);
        packData(table);
    }

    const rowMenuEdit = [
        {
            label: "Upload Data",
            menu: [
                {
                    label: "Load from CSV",
                    action: function(e, row) {
                        const table = row.getTable();
                        importCsvWithHeaders(table);
                    }
                },
                {
                    label: "Load from JSON",
                    action: function(e, row) {
                        const table = row.getTable();
                        const imported = table.import("json", ".json");
                        if (imported && typeof imported.then === "function") {
                            imported.then(function() {
                                afterTableImport(table);
                            });
                        }
                    }
                },
            ],
        },
        {
            label: "<i class='icon-add'></i> Add Row",
            action: function(e, row) {
                const table = row.getTable();
                table.addRow({}, true, row.getIndex());
            }
        },
        {
            label: "<i class='icon-subtract'></i> Delete Row",
            action: function(e, row) {
                row.delete();
            }
        },
        {
            separator: true,
        },
    ];

    const rowMenuDisplay = [
        {
            label: "Copy to Clipboard",
            action: function(e, row) {
                const table = row.getTable();
                table.copyToClipboard("all");
            }
        },
        {
            label: "Download Data",
            menu: [
                {
                    label: "Download as CSV",
                    action: function(e, row) {
                        const table = row.getTable();
                        table.download("csv", "data.csv");
                    }
                },
                {
                    label: "Download as JSON",
                    action: function(e, row) {
                        const table = row.getTable();
                        table.download("json", "data.json");
                    }
                },
                {
                    label: "Download as HTML",
                    action: function(e, row) {
                        const table = row.getTable();
                        table.download("html", "data.html");
                    }
                },
            ],
        },
    ];

    function adict2list(adict) {
        const tbl = [];
        const colnames = [];
        for (let i = 0; i < adict.length; i++) {
            const row = [];
            for (const key in adict[i]) {
                if (key === "id") {
                    continue;
                }
                row.push(adict[i][key]);
                if (i === 0) {
                    colnames.push(key);
                }
            }
            tbl.push(row);
        }
        return [tbl, colnames];
    }

    function columnTitles(dataTable) {
        return dataTable.getColumns().map(function(column) {
            return column.getDefinition().title;
        });
    }

    // Avoid browser default input size (20ch) inflating editable header widths.
    function normalizeTitleEditorSizing(scopeElem) {
        const root = scopeElem && scopeElem.querySelectorAll ? scopeElem : document;
        const editors = root.querySelectorAll('.tabulator-title-editor');
        editors.forEach(function(input) {
            const txt = String(input.value || "").trim();
            const len = txt.length > 0 ? txt.length : 2;
            input.size = Math.max(2, Math.min(24, len));
        });
    }

    // A resize submit stages its intended shape on the table element; packData
    // honors it over the (possibly already re-rendered) row/col inputs and
    // clears it once consumed. This is the single source of truth for a staged
    // resize shape - nothing else needs to know about it.
    function stagedShape(tableElem) {
        const raw = tableElem && tableElem.dataset ? tableElem.dataset.qcalc_StagedShape : null;
        return raw ? JSON.parse(raw) : null;
    }

    function pickData(dataTable, updateShape = true) {
        const tableId = dataTable.element.id;
        [tableDf[tableId], colNames[tableId]] = adict2list(dataTable.getData());
        colTitles[tableId] = columnTitles(dataTable);
        if (updateShape && !stagedShape(dataTable.element)) {
            const dataFieldId = tableDataFieldId(tableId);
            $("#" + dataFieldId + TOK_ROW).val(tableDf[tableId].length);
            $("#" + dataFieldId + TOK_COL).val(colTitles[tableId].length);
        }
    }

    function packData(dataTable) {
        const tableId = dataTable.element.id;
        const dataFieldId = tableDataFieldId(tableId);
        const edButtonId = tableControlId(tableId, TOK_TABLE_ED);
        const mode = $("#" + edButtonId).text() === "Edit" ? "display" : "edit";
        const obj = {};
        obj.data = tableDf[tableId];
        obj.columns = colTitles[tableId];
        const staged = stagedShape(dataTable.element);
        if (staged) {
            obj.shape = staged;
            delete dataTable.element.dataset.qcalc_StagedShape;
        } else {
            obj.shape = [$("#" + dataFieldId + TOK_ROW).val(), $("#" + dataFieldId + TOK_COL).val()];
        }
        obj.mode = mode;
        $("#" + dataFieldId).val(JSON.stringify(obj));
    }

    function updateTables(cid, updateShape = true) {
        const htmlTables = $(".table-responsive.table-in." + cid);
        for (let key = 0; key < htmlTables.length; key++) {
            const tableId = htmlTables[key].id;
            let foundTables = normalizeTableList(Tabulator.findTable("#" + tableId));
            if (foundTables.length === 0) {
                initTable(htmlTables[key]);
                foundTables = normalizeTableList(Tabulator.findTable("#" + tableId));
            }
            if (foundTables.length === 0) {
                continue;
            }
            let dataTable = foundTables[0];
            for (let i = 0; i < foundTables.length; i++) {
                if (foundTables[i].element && foundTables[i].element.id === tableId) {
                    dataTable = foundTables[i];
                    break;
                }
            }
            pickData(dataTable, updateShape);
            packData(dataTable);
        }
    }

    function updateAllData(jqelem, updateShape = true) {
        const cid = getCidOf(jqelem);
        updateTables(cid, updateShape);
    }

    function updateId(cid, tblidx = 0) {
        const htmlTables = $(".table-responsive.table-in." + cid);
        const tableId = htmlTables[tblidx].id;
        return tableControlId(tableId, TOK_TABLE_UPDATE);
    }

    function setUpdateButtonEnabled(tableId, enabled) {
        $("#" + tableControlId(tableId, TOK_TABLE_UPDATE)).prop("disabled", !enabled);
    }

    // Interactive mode routes normal submits to an output-only region
    // (#output-part-cid); table structural commands (Update/Resize/Edit)
    // need the whole form re-rendered, so ask the shared helper for a
    // full-form submit (qcalc.js handles the swap retarget, server routes it).
    function submitWithFullFormSwap(cid) {
        window.qcalc_FullFormSubmit(cid);
    }

    // Trial: remember local fullscreen table before structural re-render.
    function rememberFullscreenTableState(tableId) {
        const tableElem = document.getElementById(tableId);
        if (!tableElem) {
            return;
        }
        const wrapper = tableElem.closest('.elem-wrapper.table-wrap');
        const form = tableElem.closest('form');
        if (!wrapper || !form) {
            return;
        }
        if (wrapper.classList.contains('fullscreen-local')) {
            form.dataset.qcalcRestoreFullscreenTableId = tableId;
        }
    }

    // Trial: restore local fullscreen for the remembered table after form swap.
    function restoreFullscreenTableState(rootElem) {
        // htmx can pass Document as root; guard before calling Element.closest.
        const rootCanClosest = rootElem && typeof rootElem.closest === "function";
        const form = rootElem && rootElem.matches && rootElem.matches('form')
            ? rootElem
            : (rootCanClosest ? rootElem.closest('form') : null);
        if (!form) {
            return;
        }
        const tableId = form.dataset.qcalcRestoreFullscreenTableId;
        if (!tableId) {
            return;
        }
        delete form.dataset.qcalcRestoreFullscreenTableId;

        const tableElem = document.getElementById(tableId);
        if (!tableElem) {
            return;
        }
        const wrapper = tableElem.closest('.elem-wrapper.table-wrap');
        if (!wrapper) {
            return;
        }
        wrapper.classList.add('fullscreen-local');
    }

    function bindTableButtons(tableId) {
        const updateButton = $("#" + tableControlId(tableId, TOK_TABLE_UPDATE));
        if (updateButton.length > 0 && !updateButton.data("qcalc_Bound")) {
            updateButton.on("click", function() {
                const form = this.closest("form");
                const shouldResumeInteractive = form
                    && form.dataset
                    && form.dataset.interactiveEnabled === 'true';
                if (form && form.qcalcSuspendInteractive) {
                    form.qcalcSuspendInteractive();
                }
                updateAllData($(this));
                if (shouldResumeInteractive) {
                    if (form && form.qcalcResumeInteractive) {
                        form.qcalcResumeInteractive();
                    }
                    const calculateButton = form
                        ? form.querySelector('button[type="submit"]')
                        : null;
                    if (calculateButton && !calculateButton.disabled) {
                        calculateButton.click();
                    }
                }
                $(this).prop("disabled", true);
            });
            updateButton.data("qcalc_Bound", "1");
        }

        const resizeButton = $("#" + tableControlId(tableId, TOK_TABLE_RESIZE));
        if (resizeButton.length > 0 && !resizeButton.data("qcalc_Bound")) {
            resizeButton.on("click", function() {
                const form = this.closest("form");
                if (form && form.qcalcSuspendInteractive) {
                    form.qcalcSuspendInteractive();
                }
                const dataFieldId = tableDataFieldId(tableId);
                const $rowField = $("#" + dataFieldId + TOK_ROW);
                const $colField = $("#" + dataFieldId + TOK_COL);
                const clampedRow = Math.max(1, parseInt($rowField.val(), 10) || 1);
                const clampedCol = Math.max(1, parseInt($colField.val(), 10) || 1);
                $rowField.val(clampedRow);
                $colField.val(clampedCol);
                updateAllData($(this), false);
                setUpdateButtonEnabled(tableId, false);
                // stage the intended shape on the table element; packData
                // honors it over the (possibly already re-rendered) inputs
                const tableElem = document.getElementById(tableId);
                if (tableElem) {
                    tableElem.dataset.qcalc_StagedShape = JSON.stringify([String(clampedRow), String(clampedCol)]);
                }
                const cid = getCidOf($(this));
                const extraFieldId = TOK_EXTRA_PREFIX + cid;
                $("#" + extraFieldId).val(JSON.stringify({"cmd": "resize"}));
                rememberFullscreenTableState(tableId);
                submitWithFullFormSwap(cid);
            });
            resizeButton.data("qcalc_Bound", "1");
        }

        const edButton = $("#" + tableControlId(tableId, TOK_TABLE_ED));
        if (edButton.length > 0 && !edButton.data("qcalc_Bound")) {
            edButton.on("click", function() {
                const form = this.closest("form");
                if (form && form.qcalcSuspendInteractive) {
                    form.qcalcSuspendInteractive();
                }
                updateAllData($(this));
                setUpdateButtonEnabled(tableId, false);
                const cid = getCidOf($(this));
                const extraFieldId = TOK_EXTRA_PREFIX + cid;
                const extra = JSON.stringify({"cmd": this.innerText});
                $("#" + extraFieldId).val(extra);
                rememberFullscreenTableState(tableId);
                submitWithFullFormSwap(cid);
            });
            edButton.data("qcalc_Bound", "1");
        }
    }

    function bindFormSubmit(tableElem) {
        const formElem = tableElem.closest("form");
        if (!formElem) {
            return;
        }
        const $form = $(formElem);
        if ($form.data("qcalc_TableInSubmitBound")) {
            return;
        }
        $form.on("submit", function() {
            const cid = $form.find('input[name="cid"]').val() || formElem.id.replace(TOK_FORM_PREFIX, "");
            updateTables(cid);
        });
        $form.data("qcalc_TableInSubmitBound", "1");
    }

    function normalizeTableList(found) {
        if (!found) {
            return [];
        }
        if (Array.isArray(found)) {
            return found;
        }
        return [found];
    }

    function initTable(tableElem) {
        const tableId = tableElem.id;
        if (!tableId) {
            return;
        }
        const edButtonId = tableControlId(tableId, TOK_TABLE_ED);
        const mode = $("#" + edButtonId).text() === "Edit" ? "display" : "edit";
        const selector = "#" + tableId;
        const existingTables = normalizeTableList(Tabulator.findTable(selector));
        for (let i = 0; i < existingTables.length; i++) {
            if (existingTables[i].element !== tableElem) {
                existingTables[i].destroy();
            }
        }
        if (existingTables.some(function(t) { return t.element === tableElem; })) {
            bindTableButtons(tableId);
            bindFormSubmit(tableElem);
            return;
        }

        const dataTable = new Tabulator(selector, {
            pagination: "local",
            paginationSize: 10,
            paginationSizeSelector: [5, 10, 25, 50, 100, 250],
            paginationCounter: "rows",
            // Render menus in body so they are not clipped by small table wrappers.
            popupContainer: document.body,
            rowContextMenu: (mode === "edit" ? rowMenuEdit.concat(rowMenuDisplay) : rowMenuDisplay),
            columnDefaults: {
                headerSort: false,
                editor: (mode === "edit"),
                editableTitle: (mode === "edit"), // allow header rename in Edit mode
            },
            clipboard: (mode === "edit" ? true : "copy"),
            clipboardPasteAction: "replace",
        });

        setUpdateButtonEnabled(tableId, false);
        dataTable.on("cellEdited", function() {
            setUpdateButtonEnabled(tableId, true);
        });
        dataTable.on("rowAdded", function() {
            setUpdateButtonEnabled(tableId, true);
        });
        dataTable.on("rowDeleted", function() {
            setUpdateButtonEnabled(tableId, true);
        });

        dataTable.on("columnTitleChanged", function(column) {
            setUpdateButtonEnabled(tableId, true);
            const colElem = column && column.getElement ? column.getElement() : null;
            if (colElem) {
                normalizeTitleEditorSizing(colElem);
            }
        });

        dataTable.on("renderComplete", function() {
            normalizeTitleEditorSizing(this.element);
            setTimeout(() => {
                pickData(this);
                packData(this);
            }, 100);
        });

        bindTableButtons(tableId);
        bindFormSubmit(tableElem);
    }

    function initTabulatorIn(rootElem) {
        const $root = rootElem ? $(rootElem) : $(document);
        const $tables = $root.find(".table-responsive.table-in").add($root.filter(".table-responsive.table-in"));
        $tables.each(function() {
            initTable(this);
        });
    }

    window.qcalc_InitTabulatorIn = initTabulatorIn;
    window.adict2list = adict2list;
    window.updateTables = updateTables;
    window.updateAllData = updateAllData;
    window.pickData = pickData;
    window.columnTitles = columnTitles;
    window.packData = packData;
    window.updateId = updateId;

    $(document).ready(function() {
        initTabulatorIn(document);
    });

    document.body.addEventListener("htmx:afterSwap", function(evt) {
        const target = evt && evt.detail ? evt.detail.target : null;
        // outerHTML swaps leave detail.target pointing at the removed node;
        // querying it would rebuild tables against selectors missing from the live DOM.
        const root = (target && target.isConnected) ? target : document;
        initTabulatorIn(root);
        restoreFullscreenTableState(root);
    });
})();
