// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    if (window.__qcalc_ShowhideBootstrapped) {
        return;
    }
    window.__qcalc_ShowhideBootstrapped = true;

    function evaluateShowhideValue(changedVal, callback) {
        var tf_va;
        if (typeof callback === "string" && callback === "") {
            tf_va = !changedVal;
        } else if (typeof callback === "string" && callback.indexOf("@") !== -1) {
            tf_va = eval(callback.replace("@", changedVal));
        } else if (callback !== null && typeof callback === "object" && callback.constructor === Object) {
            tf_va = JSON.parse(callback[changedVal]);
        } else if (typeof window[callback] === "function") {
            tf_va = window[callback](changedVal);
        }
        return tf_va;
    }

    function bindShowhideEvent(groupId, changedId, showhideFlds, idPrefix, callback, indepFields) {
        var changedElem = document.getElementById(changedId);
        if (!changedElem) {
            return;
        }

        var token = "|" + groupId + "::" + changedId + "|";
        var boundGroups = changedElem.dataset.qcalc_ShowhideBound || "";
        if (boundGroups.indexOf(token) !== -1) {
            return;
        }

        changedElem.addEventListener("change", function(e) {
            e = e || window.event;
            var target = e.target || e.srcElement;
            var fieldElem = target || changedElem;
            var changedVal = fieldElem.value;
            var tf_va = evaluateShowhideValue(changedVal, callback);
            showhide_listof_elems_and_parts(showhideFlds, idPrefix, tf_va, indepFields);
        });

        changedElem.dataset.qcalc_ShowhideBound = boundGroups + token;
    }

    function initShowhideByCid(cid) {
        var scriptId = cid + "_script_data_showhide";
        var scriptElem = document.getElementById(scriptId);
        if (!scriptElem) {
            return;
        }

        var showhideObj = {};
        try {
            showhideObj = JSON.parse(scriptElem.textContent || "{}");
        } catch (_e) {
            return;
        }

        var idPrefix = "id_" + cid + "_";
        var indepFields = [];

        Object.entries(showhideObj).forEach(function(entry) {
            var key = entry[0];
            var value = entry[1] || {};
            if (key.endsWith("__")) {
                indepFields.push.apply(indepFields, value.fields || []);
            }
        });

        Object.entries(showhideObj).forEach(function(entry) {
            var key = entry[0];
            var value = entry[1] || {};
            if (!key.endsWith("__")) {
                var changedId = idPrefix + key;
                var showhideFlds = value.fields || [];
                var showhideCallback = ("callback" in value) ? value.callback : "";
                bindShowhideEvent(cid + "::" + key, changedId, showhideFlds, idPrefix, showhideCallback, indepFields);
            }
        });

        if (indepFields.length > 0) {
            showhide_listof_elems_and_parts(indepFields, idPrefix, false, []);
        }

        Object.entries(showhideObj).forEach(function(entry) {
            var key = entry[0];
            if (!key.endsWith("__")) {
                var changedId = idPrefix + key;
                var changedElem = document.getElementById(changedId);
                if (changedElem) {
                    changedElem.dispatchEvent(new Event("change", { bubbles: true }));
                }
            }
        });
    }

    function initShowhideInScope(rootElem) {
        var $root = rootElem ? $(rootElem) : $(document);
        var $scripts = $root
            .find('script[type="application/json"][id$="_script_data_showhide"]')
            .add($root.filter('script[type="application/json"][id$="_script_data_showhide"]'));

        $scripts.each(function() {
            var scriptId = this.id || "";
            var cid = scriptId.replace(/_script_data_showhide$/, "");
            if (cid) {
                initShowhideByCid(cid);
            }
        });
    }

    window.qcalc_InitShowhide = function(formOrElemOrCid) {
        if (typeof formOrElemOrCid === "string") {
            initShowhideByCid(formOrElemOrCid);
            return;
        }
        initShowhideInScope(formOrElemOrCid || document);
    };

    $(document).ready(function() {
        initShowhideInScope(document);
    });

    document.body.addEventListener("htmx:afterSwap", function(evt) {
        var target = evt && evt.detail ? evt.detail.target : null;
        var root = target || document;
        initShowhideInScope(root);

        // Some swap paths can leave script-data outside the immediate target.
        // Fallback keeps rebind reliable after calculate/refresh flows.
        var scopedHasData = $(root).find('script[type="application/json"][id$="_script_data_showhide"]').length > 0
            || $(root).is('script[type="application/json"][id$="_script_data_showhide"]');
        if (!scopedHasData) {
            initShowhideInScope(document);
        }
    });
})();

function showhide_elem(elem, sh)
{
    if(elem){
        if(sh){
            elem.show();
        } else {
            elem.hide();
        }
    }
    if(elem.hasClass('select2')){
        if(elem.hasClass('select2-hidden-accessible')){
            elemNext = elem.next(); //'.select2-container'
            if(elemNext){
                if(sh){
                    elemNext.show();
                } else {
                    elemNext.hide();
                }
            }
        } else {
            //selet2 control initialization yet to be completed
            //it may happen during initial page load
            setTimeout(showhide_elem, 100, elem, sh)
            //console.log('timeout')
        }
    }
}

function showhide_elem_and_parts(cid, sh)
{
    const element = $('#' + cid);
    const label = $('label[for=' + cid + ']');
    const parts = $('[id^="' + cid + '"][id*="_part"]');

    if(sh){
        element.show();
        label.show().parent().show();
    } else {
        element.hide();
        label.hide().parent().hide();
    }

    showhide_elem(element, sh)
    showhide_elem($('#'+cid+'_uom'), sh)

    parts.each(function(){
        showhide_elem($(this), sh)
    })
}

function showhide_listof_elems_and_parts(showhideFlds, id_prefix, tf_va, indepFields)
{
    for(var i=0; i<showhideFlds.length; i++){
        var cid = id_prefix+showhideFlds[i]
        // document.getElementById(cid).style.display = (tf ? 'block': 'none');
        // style.display = 'block' will result in qty field to appear in column
        // better to use jQuery .show()/.hide()
        var tf;
        if(tf_va instanceof Array){
            tf = tf_va[i]
        } else {
            tf = tf_va
        }
        // indepFields are fields that are to hidden anyway
        tf = tf && !indepFields.includes(showhideFlds[i]);
        showhide_elem_and_parts(cid, tf);
    }
}
