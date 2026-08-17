// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_TabulatorOutBootstrapped) {
        return;
    }
    window.__qcalc_TabulatorOutBootstrapped = true;

    const rowMenuDisplay = [
        {
            label: "Copy to Clipboard",
            action: function(e, row) {
                const table = row.getTable();
                table.copyToClipboard("all");
            }
        },
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
    ];

    function initTabulatorOut(rootElem) {
        const $root = rootElem ? $(rootElem) : $(document);
        const $tables = $root.find('.table-responsive.table-out').add($root.filter('.table-responsive.table-out'));

        $tables.each(function() {
            const tableElem = this;
            const tableId = tableElem.id;
            if (!tableId) {
                return;
            }

            const selector = '#' + tableId;
            const existingTables = Tabulator.findTable(selector);
            let boundToThisElem = false;

            for (let i = 0; i < existingTables.length; i++) {
                if (existingTables[i].element === tableElem) {
                    boundToThisElem = true;
                } else {
                    existingTables[i].destroy();
                }
            }

            if (boundToThisElem) {
                return;
            }

            new Tabulator(selector, {
                pagination: "local",
                paginationSize: 10,
                paginationSizeSelector: [10, 25, 50, 100],
                paginationCounter: "rows",
                //rowHeader: {formatter:"rownum", headerSort:false, hozAlign:"center", resizable:false, frozen:true},
                rowContextMenu: rowMenuDisplay,
                columnDefaults: {headerSort: false},
                clipboard: "copy",
            });
        });
    }

    window.qcalc_InitTabulatorOut = initTabulatorOut;

    $(document).ready(function() {
        initTabulatorOut(document);
    });

    document.body.addEventListener('htmx:afterSwap', function(evt) {
        const target = evt && evt.detail ? evt.detail.target : null;
        initTabulatorOut(target || document);
    });
})();
