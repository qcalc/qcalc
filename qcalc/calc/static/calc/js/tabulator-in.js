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

    function pickData(dataTable, updateShape = true) {
        const tableId = dataTable.element.id;
        [tableDf[tableId], colNames[tableId]] = adict2list(dataTable.getData());
        colTitles[tableId] = columnTitles(dataTable);
        if (updateShape) {
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
        obj.shape = [$("#" + dataFieldId + "_row").val(), $("#" + dataFieldId + "_col").val()];
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

    function bindTableButtons(tableId) {
        const updateButton = $("#id_" + tableId + "_table_update");
        if (updateButton.length > 0 && !updateButton.data("qcalc_Bound")) {
            updateButton.on("click", function() {
                updateAllData($(this));
            });
            updateButton.data("qcalc_Bound", "1");
        }

        const resizeButton = $("#id_" + tableId + "_table_resize");
        if (resizeButton.length > 0 && !resizeButton.data("qcalc_Bound")) {
            resizeButton.on("click", function() {
                updateAllData($(this), false);
                const cid = getCidOf($(this));
                const extraFieldId = "extra_" + cid;
                const calcBtnId = "calculate_" + cid;
                $("#" + extraFieldId).val(JSON.stringify({"cmd": "resize"}));
                $("#" + calcBtnId).trigger("click");
            });
            resizeButton.data("qcalc_Bound", "1");
        }

        const edButton = $("#id_" + tableId + "_table_ed");
        if (edButton.length > 0 && !edButton.data("qcalc_Bound")) {
            edButton.on("click", function() {
                updateAllData($(this));
                const cid = getCidOf($(this));
                const extraFieldId = "extra_" + cid;
                const calcBtnId = "calculate_" + cid;
                const extra = JSON.stringify({"cmd": this.innerText});
                $("#" + extraFieldId).val(extra);
                $("#" + calcBtnId).trigger("click");
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
        initTabulatorIn(target || document);
    });
})();
