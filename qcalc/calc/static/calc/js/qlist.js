// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_QlistBootstrapped) {
        return;
    }
    window.__qcalc_QlistBootstrapped = true;

    function bindQlistForm(formElem) {
        if (!formElem || formElem.dataset.qcalc_QlistBound === "1") {
            return;
        }

        formElem.addEventListener("click", function(e) {
            var target = e.target || e.srcElement;
            if (!target) {
                return;
            }

            var addButton = target.closest("button[id*='_list_add_']");
            if (addButton && formElem.contains(addButton)) {
                e.preventDefault();

                var listIdPrefix = addButton.id.replace("list_add_", "");
                var listNamePrefix = (addButton.name || "").replace("list_add_", "");
                var arrayElements = $(formElem).find("[id^='" + listIdPrefix + "']");
                if (arrayElements.length === 0) {
                    return;
                }

                var newIndex = arrayElements.length;
                var inputElement = arrayElements.last().clone();
                var lastId = inputElement.attr("id");
                var labelElement = $(formElem).find("label[for='" + lastId + "']");
                var labelPrefix = labelElement.text().replace(/\d+:$/, "");

                inputElement.attr("name", listNamePrefix + "_" + newIndex);
                inputElement.attr("id", listIdPrefix + "_" + newIndex);
                inputElement.val("");

                var newLabel = $("<label>")
                    .attr("for", inputElement.attr("id"))
                    .text(labelPrefix + newIndex + ":");
                var newDiv = $('<div class="mt-1"></div>').append(newLabel);

                arrayElements.last().after(newDiv, inputElement);
                return;
            }

            var delButton = target.closest("button[id*='_list_del_']");
            if (delButton && formElem.contains(delButton)) {
                e.preventDefault();

                var delListIdPrefix = delButton.id.replace("list_del_", "");
                var delArrayElements = $(formElem).find("[id^='" + delListIdPrefix + "']");
                if (delArrayElements.length > 1) {
                    var delInputElement = delArrayElements.last();
                    var delId = delInputElement.attr("id");
                    var delLabelElement = $(formElem).find("label[for='" + delId + "']");
                    var delLabelParent = delLabelElement.parent();

                    delInputElement.remove();
                    if (delLabelElement.length) {
                        delLabelElement.remove();
                    }
                    if (delLabelParent.length && delLabelParent.is("div")) {
                        delLabelParent.remove();
                    }
                }
            }
        });

        formElem.dataset.qcalc_QlistBound = "1";
    }

    function initQlistInScope(rootElem) {
        var $root = rootElem ? $(rootElem) : $(document);
        var $forms = $root
            .find("form[id^='form-']")
            .add($root.filter("form[id^='form-']"));

        $forms.each(function() {
            var hasQlistButtons = $(this).find("button[id*='_list_add_'], button[id*='_list_del_']").length > 0;
            if (hasQlistButtons) {
                bindQlistForm(this);
            }
        });
    }

    window.qcalc_InitQlist = function(formOrElemOrCid) {
        if (typeof formOrElemOrCid === "string") {
            var formElem = document.getElementById("form-" + formOrElemOrCid);
            if (formElem) {
                initQlistInScope(formElem);
            }
            return;
        }
        initQlistInScope(formOrElemOrCid || document);
    };

    $(document).ready(function() {
        initQlistInScope(document);
    });

    document.body.addEventListener("htmx:afterSwap", function(evt) {
        var target = evt && evt.detail ? evt.detail.target : null;
        initQlistInScope(target || document);
    });
})();
