// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

/* qCalc JavaScript */
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
    return jqelem.closest("form")[0].id.replace('form-',''); //$(this)
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

function formReady(cid) {
    $(document).ready(function() {
        function initializeSelect2(defaultValue) {
            return function() {
                var dataListId = $(this).data('list');
                var options = $('#' + dataListId + ' option');
                if($(this).hasClass('inp')){
                    drop = 'sel2-dropdown';
                } else {
                    drop = 'uom2-dropdown';
                }
                $(this).select2({
                    data: options.map(function() {
                        return { id: $(this).val(), text: $(this).text() };
                    }).get(),
                    tags: true,
                    dropdownCssClass : drop,
                });
                var newOption = new Option(defaultValue, defaultValue, true, true);
                $(this).append(newOption).trigger('change');
            }
        } // function
        $('#card-holder-'+cid).find('select.select2').each(function() {
            var defaultValue = $(this).data('default');
            $(this).each(initializeSelect2(defaultValue));
        });

        button = document.getElementById('dec-'+cid);
        if(button){ // if calculator decimal button exists on the page
            updateExtra(cid, {"ignoredec":hasIcon(button, 'icon-eye2')?"1":"0"})
        }

        elem = $('#card-holder-'+cid).find('#renderends') //renderedns time
        elem.text(Date.now()/1000);

        if (window.innerWidth <= 768) {
            addFooterClick();
        }

        si_elem = document.getElementById('searchInput');
        if (si_elem) si_elem.onkeyup = filterList;
    });
}

function initializeCodeMirrorWidget(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea || textarea.dataset.codemirrorInitialized === 'true') {
        return;
    }

    if (typeof CodeMirror === 'undefined') {
        setTimeout(function() {
            initializeCodeMirrorWidget(textareaId);
        }, 100);
        return;
    }

    const editor = CodeMirror.fromTextArea(textarea, {
        mode: 'python',
        theme: 'dracula',
        lineNumbers: true,
        matchBrackets: true,
        lineWrapping: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        extraKeys: {
            Tab: function(cm) {
                const spaces = ' '.repeat(cm.getOption('indentUnit'));
                cm.replaceSelection(spaces);
            }
        }
    });

    textarea.dataset.codemirrorInitialized = 'true';

    if (textarea.form) {
        textarea.form.addEventListener('submit', function() {
            textarea.value = editor.getValue();
        });
    }

    editor.on('blur', function() {
        textarea.value = editor.getValue();
    });

    textarea.codeMirrorEditor = editor;
}

function downloadCodeMirrorWidget(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) {
        return;
    }

    const code = textarea.codeMirrorEditor ? textarea.codeMirrorEditor.getValue() : textarea.value;
    const calNameInput = textarea.form ? textarea.form.elements.namedItem('cal_name') : null;
    const baseName = calNameInput && calNameInput.value ? calNameInput.value : 'mycal';
    const filename = baseName.replace(/[\\/:*?"<>|]/g, '_') + '.py';
    const file = new Blob([code], { type: 'text/x-python;charset=utf-8' });
    saveAs(file, filename);
}

function uploadCodeMirrorWidget(input, textareaId) {
    const file = input.files[0];
    const textarea = document.getElementById(textareaId);
    if (!file || !textarea) {
        return;
    }

    const reader = new FileReader();
    reader.onload = function() {
        const code = reader.result;
        if (textarea.codeMirrorEditor) {
            textarea.codeMirrorEditor.setValue(code);
        }
        textarea.value = code;
        input.value = '';
    };
    reader.readAsText(file);
}

function closeCard(cid)
{
    document.getElementById('card-holder-'+cid).remove();
}

function idPrefix()
{
    id_prefix = 'id_'+getCid()+ '_';
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
                if(!this.name.endsWith('_uom'))
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

var activeElement;
var clip;
function bodyFunc()
{
    curElement = document.activeElement;
    var inputs = ['input', 'textarea', 'table'];
    if (curElement && inputs.indexOf(curElement.tagName.toLowerCase()) !== -1) {
        activeElement = curElement;
    }
}

function copyText()
{
    clip = activeElement.value
    activeElement.select();
    document.execCommand('copy')
}

function uclick(unit)
{
    clip = unit
    navigator.clipboard.writeText(unit);
    sm2toggle();
}

function pasteText()
{
   activeElement.value = clip;
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
    var top = document.getElementById('card-holder-'+lastCid).offsetTop; //Getting Y of target element
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
    var el = document.getElementById('card-holder-'+cid);
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
  var el = document.getElementById('card-holder-'+cid);
  if(el !== null){
    jumpTo(cid); // move to the card
    return false;  // no need to get
  } else {
    return true; // get the card
  }
}

function updateExtra(cid,dict){
    extra_field_id = "extra_" + cid;
    extra_cur_val = $('#'+extra_field_id).val();
    if (extra_cur_val == null) extra_cur_val = "{}";
    let oriObj = JSON.parse(extra_cur_val);

    if (dict == null) dict = "{}";
    let newObj = dict;

    extra_new_val = JSON.stringify(Object.assign(oriObj, newObj));
    $('#'+extra_field_id).val(extra_new_val);
    //console.log($('#'+extra_field_id).val());
}

function calClick(cid){
    calc_btn_id = "calculate_" + cid;
    $('#'+calc_btn_id).trigger('click');
}

function calWithCmd(cid, fname, cmd){ // cmd='save_input', 'save_io', 'save_var', 'create_var'
    updateExtra(cid,{"cmd":cmd});
    calClick(cid);
}

function saveInput(fname){ // cmd='save_input', 'save_io', 'save_var', 'create_var'
    var xhr = new XMLHttpRequest();
    xhr.open("POST", '/calc/save/');
    xhr.responseType = 'blob';
    var csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value;
    xhr.setRequestHeader('X-CSRFToken', csrftoken);
    xhr.onload = function() {
        saveAs(xhr.response, fname+'.json'); //FileSaver.min.js
    }
    xhr.send();
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
//fileinput( document, window, 0 );

document.addEventListener('DOMContentLoaded', function() {
    fileinput(document, window, 0);
});

function toggleFullscreen(elem) {
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

function qmdCopyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    }

    return new Promise(function(resolve, reject) {
        var area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', 'readonly');
        area.style.position = 'fixed';
        area.style.opacity = '0';
        document.body.appendChild(area);
        area.select();
        try {
            document.execCommand('copy');
            resolve();
        } catch (err) {
            reject(err);
        } finally {
            document.body.removeChild(area);
        }
    });
}

function qmdEnhanceCodeBlocks(root) {
    var scope = root || document;
    var blocks = scope.querySelectorAll('.md-content pre');

    blocks.forEach(function(pre) {
        if (pre.querySelector('.qmd-copy-btn')) {
            return;
        }

        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'qmd-copy-btn';
        button.innerHTML = '<i class="icon-files-empty" aria-hidden="true"></i>';
        button.setAttribute('aria-label', 'Copy code block');
        button.setAttribute('title', 'Copy');

        button.addEventListener('click', function() {
            var code = pre.querySelector('code');
            var text = code ? code.innerText : pre.innerText;
            qmdCopyText(text).then(function() {
                button.classList.add('qmd-copy-ok');
                button.setAttribute('title', 'Copied');
                window.setTimeout(function() {
                    button.classList.remove('qmd-copy-ok');
                    button.setAttribute('title', 'Copy');
                    button.blur();
                }, 500);
            }).catch(function() {
                button.classList.add('qmd-copy-fail');
                button.setAttribute('title', 'Copy failed');
                window.setTimeout(function() {
                    button.classList.remove('qmd-copy-fail');
                    button.setAttribute('title', 'Copy');
                    button.blur();
                }, 500);
            });
        });

        pre.appendChild(button);
    });
}

function qmdEnhanceImages(root) {
    var scope = root || document;
    var images = scope.querySelectorAll('.md-content img:not(.qmd-img-wrapper img)');

    images.forEach(function(img) {
        if (img.closest('.qmd-img-wrapper')) {
            return;
        }
        var wrapper = document.createElement('span');
        wrapper.className = 'qmd-img-wrapper';
        img.parentNode.insertBefore(wrapper, img);
        wrapper.appendChild(img);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    qmdEnhanceCodeBlocks(document);
    qmdEnhanceImages(document);
    if (document.body) {
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            qmdEnhanceCodeBlocks(evt.target);
            qmdEnhanceImages(evt.target);
        });
    }
});

