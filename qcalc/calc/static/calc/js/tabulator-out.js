// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_TabulatorOutBootstrapped) {
        return;
    }
    window.__qcalc_TabulatorOutBootstrapped = true;

    // Tabulator reads cells of a server-rendered <table> via innerHTML, so pandas' HTML
    // entities (e.g. &amp;) arrive in the data. Decode them once so cells and exports are plain text.
    function decodeHtmlEntities(data) {
        if (!Array.isArray(data)) {
            return;
        }
        const decoder = document.createElement('textarea');
        data.forEach(function(row) {
            Object.keys(row).forEach(function(key) {
                if (typeof row[key] === 'string' && row[key].indexOf('&') !== -1) {
                    decoder.innerHTML = row[key];
                    row[key] = decoder.value;
                }
            });
        });
    }

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
            if (!tableId || !tableElem.isConnected) {
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

            // Build Tabulator options and allow printable-flat mode to disable pagination.
            const tabOpts = {
                // Render menus in body so they are not clipped by small table wrappers.
                popupContainer: document.body,
                rowContextMenu: rowMenuDisplay,
                columnDefaults: {headerSort: false},
                clipboard: "copy",
            };
            try {
                if (!window.__qcalc_tabulator_print_all && tableElem.dataset.pageAll !== "true") {
                    tabOpts.pagination = "local";
                    tabOpts.paginationSize = 10;
                    tabOpts.paginationSizeSelector = [5, 10, 25, 50, 100, 250];
                    tabOpts.paginationCounter = "rows";
                } else {
                    tabOpts.pagination = false;
                }
            } catch (e) {
                // default to pagination on error
                tabOpts.pagination = "local";
                tabOpts.paginationSize = 10;
                tabOpts.paginationSizeSelector = [5, 10, 25, 50, 100, 250];
                tabOpts.paginationCounter = "rows";
            }
            const outTable = new Tabulator(tableElem, tabOpts);
            outTable.on("dataLoading", decodeHtmlEntities);
        });
    }

    window.qcalc_InitTabulatorOut = initTabulatorOut;

    $(document).ready(function() {
        initTabulatorOut(document);
    });

    document.body.addEventListener('htmx:afterSwap', function(evt) {
        const target = evt && evt.detail ? evt.detail.target : null;
        // outerHTML swaps leave detail.target pointing at the removed node;
        // querying it would rebuild tables against selectors missing from the live DOM.
        const root = (target && target.isConnected) ? target : document;
        initTabulatorOut(root);
    });
})();
