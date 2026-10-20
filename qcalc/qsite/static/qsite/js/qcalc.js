// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

/* qCalc JavaScript */

const QCALC_TOK_TABLE_UPDATE = '_table_update';
const QCALC_TOK_UOM = '_uom';
const QCALC_TOK_FORM_PREFIX = 'form-';
const QCALC_TOK_OUTPUT_PREFIX = '#output-part-';
const QCALC_TOK_CARD_PREFIX = 'card-holder-';
const QCALC_TOK_ID_PREFIX = 'id_';
const QCALC_TOK_FIELD_SEP = '_';

// ---- structural (full-form) submit machinery ---------------------------
// A "structural" submit is one whose response must replace the WHOLE form
// (e.g. input-table Resize/Edit re-renders the table's own markup), as
// opposed to a normal submit whose response only refreshes the output
// region (#output-part-<cid>).
(function() {
    function qcalcRequestPath(detail, trigger) {
        var requestPath = detail.path || (detail.pathInfo && detail.pathInfo.requestPath) || '';
        if (requestPath) {
            return requestPath;
        }
        var host = trigger && trigger.closest ? trigger.closest('[hx-get]') : null;
        return host ? (host.getAttribute('hx-get') || '') : '';
    }

    function qcalcRequestedFunc(detail, trigger) {
        var params = detail.parameters || (detail.requestConfig && detail.requestConfig.parameters) || {};
        var fname = (params['fname'] || '').toString().trim().toLowerCase();
        if (fname) {
            return fname;
        }

        var pathArg = (params['path'] || '').toString().trim();
        if (pathArg) {
            return pathArg.split('/')[0].trim().toLowerCase();
        }

        var requestPath = qcalcRequestPath(detail, trigger);
        if (!requestPath) {
            return '';
        }

        try {
            var url = new URL(requestPath, window.location.origin);
            var queryFname = (url.searchParams.get('fname') || '').trim().toLowerCase();
            if (queryFname) {
                return queryFname;
            }
            var queryPath = (url.searchParams.get('path') || '').trim();
            if (queryPath) {
                return queryPath.split('/')[0].trim().toLowerCase();
            }
        } catch (_err) {
            return '';
        }

        return '';
    }

    function qcalcFindOpenSingleton(funcName) {
        var cards = document.querySelectorAll('[id^="' + QCALC_TOK_CARD_PREFIX + '"][data-qcalc-single-instance="1"]');
        for (var i = 0; i < cards.length; i++) {
            var card = cards[i];
            var cardFunc = (card.dataset.qcalcFunc || '').trim().toLowerCase();
            if (cardFunc === funcName) {
                return card;
            }
        }
        return null;
    }

    document.addEventListener('htmx:configRequest', function(event) {
        var detail = event.detail || {};
        var reqPath = qcalcRequestPath(detail, event.target);
        if (reqPath.includes('/calc/add')) {
            var requestedFunc = qcalcRequestedFunc(detail, event.target);
            if (requestedFunc) {
                var existing = qcalcFindOpenSingleton(requestedFunc);
                if (existing) {
                    var existingCid = existing.dataset.qcalcCid || existing.id.replace(QCALC_TOK_CARD_PREFIX, '');
                    jumpTo(existingCid);
                    event.preventDefault();
                    return;
                }
            }
        }

        var params = detail.parameters || {};
        if (params['qcalc_structural_cmd'] !== '1') {
            return;
        }
        var form = event.target && event.target.tagName === 'FORM'
            ? event.target
            : (event.target && event.target.closest ? event.target.closest('form') : null);
        if (!form) {
            return;
        }
        detail.headers = detail.headers || {};
        detail.headers['X-QCalc-Structural-Cmd'] = '1';
        // the form is about to be replaced; re-allow live calculation on
        // the replacement form (undoes any earlier qcalcSuspendInteractive)
        form.dataset.interactiveEnabled = 'true';
    });

    // After a structural (full-form) swap completes, restore the form's
    // normal output-part targeting so subsequent ordinary submits go back
    // to partial refresh (the helper mutated it to hx-target=this).
    document.addEventListener('htmx:afterSwap', function(event) {
        var form = event.detail && event.detail.target;
        if (!form || form.tagName !== 'FORM') {
            return;
        }
        if (form.getAttribute('hx-target') !== 'this') {
            return;
        }
        var cid = form.id.replace(QCALC_TOK_FORM_PREFIX, '');
        form.setAttribute('hx-target', QCALC_TOK_OUTPUT_PREFIX + cid);
        form.setAttribute('hx-swap', 'outerHTML');
        form.removeAttribute('hx-vals');
    });

})();

var jsCid = '-';
function setCid(cid)
{
   jsCid = cid;
}

function getCid() //use this function only when document is ready otherwise cid can be wrong
{
    if(jsCid == '-') //not set, this block is safeguard but really shouldn't be necessary
    //if qcalc.js (where setCid/getCid is defined) is loaded without defer - getCid will always have the cid
    {
        cidLast = document.getElementsByName('cid').length - 1;//warning: cal may not be added to the last
        jsCid = document.getElementsByName('cid')[cidLast].value;
    }
   return jsCid;
}

function getCidOf(jqelem) //can use anytime, get cid knowing an element inside the form having cid in it's id
{
    return jqelem.closest("form")[0].id.replace(QCALC_TOK_FORM_PREFIX,''); //$(this)
}

function getCidFrom(jqelem, parentElemClass, parentIdPrefix) //can use anytime, get cid knowing an element inside a parent having cid in it's id
{
    return jqelem.closest('.'+parentElemClass)[0].id.replace(parentIdPrefix,''); //$(this)
}

function setCidFrom(jqelem, parentElemClass, parentIdPrefix) { // use it to asign cid value to a link element dynamically on page
    var cidValue = getCidFrom(jqelem, parentElemClass, parentIdPrefix);
    jqelem.attr('hx-vals', JSON.stringify({ cid: cidValue }));
    return true; // improtant to continue with htmx-get event
}

function toggleLoadButton()
{
    const fileInput = document.getElementById('open-io');
    const loadButton = document.getElementById('load-io');
    loadButton.disabled = !fileInput.files.length; // Enable button if a file is selected
}

function qcalc_EnableTableUpdateAfterSwap(cid) {
    const swapSync = function(evt) {
        const target = evt && evt.detail ? evt.detail.target : null;
        if (!target || target.id !== (QCALC_TOK_FORM_PREFIX + cid)) {
            return;
        }
        document.body.removeEventListener("htmx:afterSwap", swapSync);
        setTimeout(function() {
            const form = document.getElementById(QCALC_TOK_FORM_PREFIX + cid);
            if (!form) {
                return;
            }
            const updateBtn = form.querySelector("button[id$='" + QCALC_TOK_TABLE_UPDATE + "']");
            if (updateBtn) {
                updateBtn.disabled = false;
            }
        }, 0);
    };
    document.body.addEventListener("htmx:afterSwap", swapSync);
}

function formReady(cid) {
    $(document).ready(function() {
        function preserveReadonlySelect($sel) {
            var name = $sel.attr('name');
            var value = $sel.val();
            $sel.prop('disabled', true);
            $sel.removeAttr('readonly');
            if (name) {
                $sel.removeAttr('name');
                if ($sel.prop('multiple')) {
                    var values = Array.isArray(value) ? value : [value];
                    values.forEach(function(v) {
                        if (v !== null && v !== undefined && v !== '') {
                            $('<input type="hidden" />')
                                .attr('name', name)
                                .val(v)
                                .insertBefore($sel);
                        }
                    });
                } else if (value !== null && value !== undefined && value !== '') {
                    $('<input type="hidden" />')
                        .attr('name', name)
                        .val(value)
                        .insertBefore($sel);
                }
            }
        }

        function initializeSelect2(defaultValue) {
            return function() {
                var $sel = $(this);
                var isReadOnly = $sel.attr('readonly') !== undefined || $sel.data('readonly') === true;

                if (isReadOnly) {
                    preserveReadonlySelect($sel);
                    return;
                }

                var dataListId = $sel.data('list');
                var options = $('#' + dataListId + ' option');
                if($sel.hasClass('inp')){
                    drop = 'sel2-dropdown';
                } else {
                    drop = 'uom2-dropdown';
                }
                $sel.select2({
                    data: options.map(function() {
                        return { id: $(this).val(), text: $(this).text() };
                    }).get(),
                    tags: true,
                    dropdownCssClass : drop,
                });
                var newOption = new Option(defaultValue, defaultValue, true, true);
                $sel.append(newOption).trigger('change');
            }
        } // function
        $('#' + QCALC_TOK_CARD_PREFIX + cid).find('select').each(function() {
            var $sel = $(this);
            var isReadOnly = $sel.attr('readonly') !== undefined || $sel.data('readonly') === true;
            if (isReadOnly) {
                preserveReadonlySelect($sel);
                return;
            }
            if ($sel.hasClass('select2')) {
                var defaultValue = $sel.data('default');
                $sel.each(initializeSelect2(defaultValue));
            }
        });

        button = document.getElementById('dec-'+cid);
        if(button){ // if calculator decimal button exists on the page
            if (window.QCalcActions && window.QCalcActions.updateExtra) {
                window.QCalcActions.updateExtra(cid, {"ignoredec":hasIcon(button, 'icon-eye2')?"1":"0"});
            }
        }

        elem = $('#' + QCALC_TOK_CARD_PREFIX + cid).find('#renderends') //renderedns time
        elem.text(Date.now()/1000);

        if (window.innerWidth <= 768) {
            addFooterClick();
        }

        si_elem = document.getElementById('searchInput');
        if (si_elem) si_elem.onkeyup = filterList;
    });
}

function closeCard(cid)
{
    var card = document.getElementById(QCALC_TOK_CARD_PREFIX + cid);
    if (!card) {
        return;
    }

    var form = document.getElementById(QCALC_TOK_FORM_PREFIX + cid);
    var tokenInput = form ? form.querySelector('input[name="csrfmiddlewaretoken"]') : null;

    if (tokenInput && tokenInput.value) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/calc/io/clear/' + encodeURIComponent(cid) + '/');
        xhr.setRequestHeader('X-CSRFToken', tokenInput.value);
        xhr.send();
    } else {
        var xhrFallback = new XMLHttpRequest();
        xhrFallback.open('GET', '/calc/io/clear/' + encodeURIComponent(cid) + '/');
        xhrFallback.send();
    }

    card.remove();
}

function idPrefix()
{
    id_prefix = QCALC_TOK_ID_PREFIX + getCid() + QCALC_TOK_FIELD_SEP;
    return id_prefix;
}

function showDiv(divId) {
  var x = document.getElementById(divId);
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}

function clearForm(ele) {
    $(ele).find(':input').each(function() {
        switch(this.type) {
            case 'password':
            case 'select-multiple':
            case 'select-one':
            case 'number':
            case 'text':
            case 'textarea':
                if(!this.name.endsWith(QCALC_TOK_UOM))
                    $(this).val('');
                break;
            case 'checkbox':
            case 'radio':
                this.checked = false;
                break;
            default:
                break;
        }
    });

    $(ele).find('.CodeMirror').each(function() {
        this.CodeMirror.setValue("");
        this.focus();
    });
}

function toggleIcon(button, icon1, icon2) {
  var icon = button.querySelector('i');
  if (icon.classList.contains(icon1)) {
    icon.classList.remove(icon1);
    icon.classList.add(icon2);
    val = 2;
  } else {
    icon.classList.remove(icon2);
    icon.classList.add(icon1);
    val = 1;
  }
  return val;
}

function hasIcon(button, icon1) {
  var icon = button.querySelector('i');
  return icon.classList.contains(icon1);
}

function chainEvent(elementId, eventName, eventFn)
{
    var element = document.getElementById(elementId);
    var onEventName = "on"+eventName
    if(element.addEventListener){
      element.addEventListener(eventName, eventFn, false);
    }
    else if(element.attachEvent){
      element.attachEvent(onEventName, eventFn);
    }
}

function sm2toggle()
{
    document.querySelector('.sidebar-mobile-secondary-toggle').click();
}

function jumpLast(){ // jump to last card
    //dynamically determine last cid added, because it needs to work within htmx.on event
    //lastCid = jsCid won't work, the event will always use the very first assigned value
    cidLast = document.getElementsByName('cid').length - 1;
    lastCid = document.getElementsByName('cid')[cidLast].value;
    var top = document.getElementById(QCALC_TOK_CARD_PREFIX + lastCid).offsetTop; //Getting Y of target element
    window.scrollTo(0, top);
}

function jumpBottom(){ // jump to bottom of the screen
    var top = document.getElementById('card-space').offsetTop; //Getting Y of target element
    window.scrollTo(0, top);
}
function jumpTop(){ // jump to top of the screen
    var top = document.getElementById('head-home').offsetBottom; //Getting Y of target element
    window.scrollTo(0, top);
}

function jumpFirst(){ // jump to first card
    var top = document.getElementById('content-holder').offsetTop; //Getting Y of target element
    window.scrollTo(0, top);
}

function elementIsVisibleInViewport(el, visibility = 2){
//1=top or bottom within screen, 2=center within screen, 3 = whole within screen
// courtesy: https://www.30secondsofcode.org/js/s/element-is-visible-in-viewport/
  const { top, left, bottom, right } = el.getBoundingClientRect();
  const { innerHeight, innerWidth } = window;
  if(visibility==1){
    return ((top > 0 && top < innerHeight) ||
      (bottom > 0 && bottom < innerHeight)) &&
      ((left > 0 && left < innerWidth) || (right > 0 && right < innerWidth))
  }else if(visibility==2){
    cy = (top+bottom)/2;
    cx = (left+right)/2;
    return cy >= 0 && cx >= 0 && cy <= innerHeight && cx <= innerWidth;
  }else{
    return top >= 0 && left >= 0 && bottom <= innerHeight && right <= innerWidth;
  }
}

function jumpTo(cid){ // jump to card having cid
    var el = document.getElementById(QCALC_TOK_CARD_PREFIX + cid);
    if(!elementIsVisibleInViewport(el, 2)){
        var top = el.offsetTop;
        window.scrollTo(0, top);
    }
}

function jumpToElemId(elemId){ // jump to element id
    var el = document.getElementById(elemId);
    if(!elementIsVisibleInViewport(el, 2)){
        var top = el.offsetTop;
        window.scrollTo(0, top);
    }
}

function get_card_once(cid){
    var el = document.getElementById(QCALC_TOK_CARD_PREFIX + cid);
  if(el !== null){
    jumpTo(cid); // move to the card
    return false;  // no need to get
  } else {
    return true; // get the card
  }
}

function validateFileSize(input, max_mb=10.0) {
    const file = input.files[0];
    const maxSize = Math.ceil(max_mb * 1024 * 1024); // default 10 MB in bytes
    if (file.size > maxSize) {
        alert("File size must be less than "+max_mb+" MB.");
        input.value = ''; // Clear the input
    }
}

function addFooterClick() {
    //document.addEventListener('DOMContentLoaded', function() {
    const button = document.querySelector('.navbar-toggler.dropdown-toggle');
    const footer = document.getElementById('navbar-footer'); // Ensure your footer has this ID

    button.addEventListener('click', function() {
        setTimeout(() => { // Timeout to wait for the collapse animation to complete
            if (!footer.classList.contains('collapsing')) {
                footer.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        }, 350); // Adjust timeout based on your collapse animation duration
    });
    //});
}

/*
	fileinput: By Osvaldas Valutis, www.osvaldas.info
	Available for use under the MIT License
*/

function fileinput( document, window, index )
{
	var inputs = document.querySelectorAll( '.inputfile' );
	Array.prototype.forEach.call( inputs, function( input )
	{
		var label	 = input.nextElementSibling,
			labelVal = label.innerHTML;

		input.addEventListener( 'change', function( e )
		{
			var fileName = '';
			if( this.files && this.files.length > 1 )
				fileName = ( this.getAttribute( 'data-multiple-caption' ) || '' ).replace( '{count}', this.files.length );
			else
				fileName = e.target.value.split( '\\' ).pop();

			if( fileName )
				label.querySelector( 'span' ).innerHTML = fileName;
			else
				label.innerHTML = labelVal;
		});
	});
}

document.addEventListener('DOMContentLoaded', function() {
    fileinput(document, window, 0);
});

function toggleFullscreen(elem) {
    // Table wrappers use local fullscreen to avoid flicker on form re-render.
    if (elem && elem.classList && elem.classList.contains('table-wrap')) {
        elem.classList.toggle('fullscreen-local');
        return;
    }

    if (!document.fullscreenElement) {
        elem.classList.add('fullscreen');
        elem.requestFullscreen().catch(err => {
            alert(`Error attempting to enable fullscreen: ${err.message}`);
        });
    } else {
        document.exitFullscreen().then(() => {
            elem.classList.remove('fullscreen');
        });
    }
}

// Escape closes only local table fullscreen overlays; browser fullscreen keeps its own ESC behavior.
document.addEventListener('keydown', function(event) {
    if (event.key !== 'Escape') {
        return;
    }

    const localFullscreen = document.querySelector('.elem-wrapper.table-wrap.fullscreen-local');
    if (!localFullscreen) {
        return;
    }

    localFullscreen.classList.remove('fullscreen-local');
});


function themeChanger(themeSelectorElemId){
    document.getElementById(themeSelectorElemId).addEventListener('change', function() {
      var selectedTheme = this.value;
      var themeStylesheets = document.querySelectorAll('.theme-stylesheet');

      themeStylesheets.forEach(function(link) {
        // Get the current href of the stylesheet
        var currentHref = link.getAttribute('href');

        // Replace the current theme name (e.g., "default") with the new theme name
        var newHref = currentHref.replace(/(.*-)\w+(\.css)/, `$1${selectedTheme}$2`);
        // Update the href with the new theme
        link.setAttribute('href', newHref);
      });
    });
}

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
          // Check if this cookie string begins with the given name
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}

function setCustomAttributes(elementId, attributes) {
    var element = document.getElementById(elementId);
    for (var attr in attributes) {
        if (attributes.hasOwnProperty(attr)) {
            element.setAttribute(attr, attributes[attr]);
        }
    }
}
