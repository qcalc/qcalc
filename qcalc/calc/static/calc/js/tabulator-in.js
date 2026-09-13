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

    const rowMenuEdit = [
        {
            label: "Upload Data",
            menu: [
                {
                    label: "Load from CSV",
                    action: function(e, row) {
                        const table = row.getTable();
                        table.import("csv", [".csv", ".txt"]);
                    }
                },
                {
                    label: "Load from JSON",
                    action: function(e, row) {
                        const table = row.getTable();
                        table.import("json", ".json");
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
            const dataFieldId = "id_" + tableId;
            $("#" + dataFieldId + "_row").val(tableDf[tableId].length);
            $("#" + dataFieldId + "_col").val(colTitles[tableId].length);
        }
    }

    function packData(dataTable) {
        const tableId = dataTable.element.id;
        const dataFieldId = "id_" + tableId;
        const edButtonId = "id_" + tableId + "_table_ed";
        const mode = $("#" + edButtonId).text() === "Edit" ? "display" : "edit";
        const obj = {};
        obj.data = tableDf[tableId];
        obj.columns = colTitles[tableId];
        const staged = stagedShape(dataTable.element);
        if (staged) {
            obj.shape = staged;
            delete dataTable.element.dataset.qcalc_StagedShape;
        } else {
            obj.shape = [$("#" + dataFieldId + "_row").val(), $("#" + dataFieldId + "_col").val()];
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
        return "id_" + tableId + "_table_update";
    }

    function setUpdateButtonEnabled(tableId, enabled) {
        $("#id_" + tableId + "_table_update").prop("disabled", !enabled);
    }

    // Interactive mode routes normal submits to an output-only region
    // (#output-part-cid); table structural commands (Update/Resize/Edit)
    // need the whole form re-rendered, so ask the shared helper for a
    // full-form submit (qcalc.js handles the swap retarget, server routes it).
    function submitWithFullFormSwap(cid) {
        window.qcalc_FullFormSubmit(cid);
    }

    function bindTableButtons(tableId) {
        const updateButton = $("#id_" + tableId + "_table_update");
        if (updateButton.length > 0 && !updateButton.data("qcalc_Bound")) {
            updateButton.on("click", function() {
                const form = this.closest("form");
                if (form && form.qcalcSuspendInteractive) {
                    form.qcalcSuspendInteractive();
                }
                updateAllData($(this));
                $(this).prop("disabled", true);
            });
            updateButton.data("qcalc_Bound", "1");
        }

        const resizeButton = $("#id_" + tableId + "_table_resize");
        if (resizeButton.length > 0 && !resizeButton.data("qcalc_Bound")) {
            resizeButton.on("click", function() {
                const form = this.closest("form");
                if (form && form.qcalcSuspendInteractive) {
                    form.qcalcSuspendInteractive();
                }
                const $rowField = $("#id_" + tableId + "_row");
                const $colField = $("#id_" + tableId + "_col");
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
                const extraFieldId = "extra_" + cid;
                $("#" + extraFieldId).val(JSON.stringify({"cmd": "resize"}));
                submitWithFullFormSwap(cid);
            });
            resizeButton.data("qcalc_Bound", "1");
        }

        const edButton = $("#id_" + tableId + "_table_ed");
        if (edButton.length > 0 && !edButton.data("qcalc_Bound")) {
            edButton.on("click", function() {
                const form = this.closest("form");
                if (form && form.qcalcSuspendInteractive) {
                    form.qcalcSuspendInteractive();
                }
                updateAllData($(this));
                setUpdateButtonEnabled(tableId, false);
                const cid = getCidOf($(this));
                const extraFieldId = "extra_" + cid;
                const extra = JSON.stringify({"cmd": this.innerText});
                $("#" + extraFieldId).val(extra);
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
            const cid = $form.find('input[name="cid"]').val() || formElem.id.replace("form-", "");
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
        const edButtonId = "id_" + tableId + "_table_ed";
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
            paginationSizeSelector: [10, 25, 50, 100],
            paginationCounter: "rows",
            rowContextMenu: (mode === "edit" ? rowMenuEdit.concat(rowMenuDisplay) : rowMenuDisplay),
            columnDefaults: {headerSort: false, editor: (mode === "edit")},
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

        dataTable.on("renderComplete", function() {
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
    });
})();
