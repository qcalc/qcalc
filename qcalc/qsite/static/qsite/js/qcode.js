// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

/* qCalc code widget JavaScript */

(function() {
    const QCODE_CARD_PREFIX = 'card-holder-';

    function normalizeCodeLanguage(language) {
        const lang = (language || '').trim().toLowerCase();
        const aliases = {
            py: 'python',
            python3: 'python',
            ht: 'html',
            htm: 'html',
            xhtml: 'html',
            md: 'markdown',
            js: 'javascript',
            mjs: 'javascript'
        };
        if (aliases[lang]) {
            return aliases[lang];
        }
        return lang || 'python';
    }

    function codeMirrorMode(language) {
        const modeByLanguage = {
            python: 'python',
            html: 'htmlmixed',
            markdown: 'markdown',
            javascript: 'javascript'
        };
        return modeByLanguage[language] || 'python';
    }

    function codeFileSpec(language) {
        const specByLanguage = {
            python: { extension: '.py', mime: 'text/x-python', accept: '.py,text/x-python,text/plain' },
            html: { extension: '.html', mime: 'text/html', accept: '.html,.htm,text/html,text/plain' },
            markdown: { extension: '.md', mime: 'text/markdown', accept: '.md,.markdown,text/markdown,text/plain' },
            javascript: { extension: '.js', mime: 'text/javascript', accept: '.js,.mjs,text/javascript,application/javascript,text/plain' }
        };
        return specByLanguage[language] || specByLanguage.python;
    }

    function toggleWrapperFullscreen(wrapper) {
        if (!wrapper) {
            return;
        }

        if (typeof window.toggleFullscreen === 'function') {
            window.toggleFullscreen(wrapper);
            return;
        }

        if (!document.fullscreenElement) {
            wrapper.classList.add('fullscreen');
            if (wrapper.requestFullscreen) {
                wrapper.requestFullscreen().catch(function(err) {
                    alert('Error attempting to enable fullscreen: ' + err.message);
                });
            }
            return;
        }

        if (document.exitFullscreen) {
            document.exitFullscreen().then(function() {
                wrapper.classList.remove('fullscreen');
            });
        } else {
            wrapper.classList.remove('fullscreen');
        }
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

        const language = normalizeCodeLanguage(textarea.dataset.lang || 'python');
        textarea.dataset.lang = language;
        const fileSpec = codeFileSpec(language);
        const uploadInput = document.getElementById(textareaId + '_upload');
        if (uploadInput) {
            uploadInput.accept = fileSpec.accept;
        }

        const editor = CodeMirror.fromTextArea(textarea, {
            mode: codeMirrorMode(language),
            theme: 'dracula',
            lineNumbers: true,
            matchBrackets: true,
            autoCloseBrackets: true,
            lineWrapping: true,
            indentUnit: 4,
            tabSize: 4,
            indentWithTabs: false,
            extraKeys: {
                Tab: function(cm) {
                    if (cm.somethingSelected()) {
                        cm.indentSelection('add');
                        return;
                    }
                    cm.replaceSelection(' '.repeat(cm.getOption('indentUnit')), 'end');
                },
                'Shift-Tab': function(cm) {
                    if (cm.somethingSelected()) {
                        cm.indentSelection('subtract');
                        return;
                    }
                    cm.indentLine(cm.getCursor().line, 'subtract');
                },
                'Ctrl-S': function() {
                    downloadCodeMirrorWidget(textareaId);
                },
                'Cmd-S': function() {
                    downloadCodeMirrorWidget(textareaId);
                },
                F11: function(cm) {
                    const wrapper = textarea.closest('.elem-wrapper');
                    toggleWrapperFullscreen(wrapper);
                    setTimeout(function() {
                        cm.refresh();
                    }, 100);
                }
            }
        });

        textarea.dataset.codemirrorInitialized = 'true';

        if (typeof ResizeObserver !== 'undefined') {
            new ResizeObserver(function() {
                editor.refresh();
            }).observe(editor.getWrapperElement());
        }

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

    function closeCodeMirrorWidgetMenus(exceptMenuId) {
        const menus = document.querySelectorAll('.code-widget-menu-panel.show');
        menus.forEach(function(menu) {
            if (exceptMenuId && menu.id === exceptMenuId) {
                return;
            }
            menu.classList.remove('show');
        });
    }

    function toggleCodeMirrorWidgetMenu(button, menuId) {
        const menu = document.getElementById(menuId);
        if (!menu) {
            return;
        }

        const shouldOpen = !menu.classList.contains('show');
        closeCodeMirrorWidgetMenus(menuId);
        if (shouldOpen) {
            menu.classList.add('show');
        } else {
            menu.classList.remove('show');
        }

        if (!window._codeMirrorWidgetMenuBound) {
            document.addEventListener('click', function(event) {
                if (event.target.closest('.code-widget-menu')) {
                    return;
                }
                closeCodeMirrorWidgetMenus();
            });
            window._codeMirrorWidgetMenuBound = true;
        }
    }

    function getCodeMirrorWidgetText(textarea) {
        if (!textarea) {
            return '';
        }
        return textarea.codeMirrorEditor ? textarea.codeMirrorEditor.getValue() : textarea.value;
    }

    function setCodeMirrorWidgetText(textarea, text) {
        if (!textarea) {
            return;
        }
        const nextText = text || '';
        if (textarea.codeMirrorEditor) {
            textarea.codeMirrorEditor.setValue(nextText);
        }
        textarea.value = nextText;
    }

    function copyCodeMirrorWidget(textareaId) {
        const textarea = document.getElementById(textareaId);
        if (!textarea) {
            return Promise.resolve();
        }

        const code = getCodeMirrorWidgetText(textarea);
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(code);
        }

        return new Promise(function(resolve, reject) {
            const area = document.createElement('textarea');
            area.value = code;
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

    function pasteReplaceCodeMirrorWidget(textareaId) {
        const textarea = document.getElementById(textareaId);
        if (!textarea) {
            return Promise.resolve();
        }
        if (textarea.disabled || textarea.readOnly) {
            return Promise.resolve();
        }

        const applyText = function(pasteText) {
            if (pasteText === null || pasteText === undefined) {
                return;
            }
            const currentCode = getCodeMirrorWidgetText(textarea);
            if (currentCode && currentCode.trim() && currentCode !== pasteText) {
                if (!confirm('Replace existing code with pasted content?')) {
                    return;
                }
            }
            setCodeMirrorWidgetText(textarea, pasteText);
        };

        if (navigator.clipboard && navigator.clipboard.readText) {
            return navigator.clipboard.readText()
                .then(function(text) {
                    applyText(text);
                })
                .catch(function() {
                    const pasted = prompt('Paste code to replace current content:', '');
                    applyText(pasted);
                });
        }

        const pasted = prompt('Paste code to replace current content:', '');
        applyText(pasted);
        return Promise.resolve();
    }

    function clearCodeMirrorWidget(textareaId) {
        const textarea = document.getElementById(textareaId);
        if (!textarea) {
            return;
        }
        if (textarea.disabled || textarea.readOnly) {
            return;
        }
        const code = getCodeMirrorWidgetText(textarea);
        if (code && code.trim() && !confirm('Clear all code?')) {
            return;
        }
        setCodeMirrorWidgetText(textarea, '');
    }

    function codeMirrorWidgetMenuAction(textareaId, action) {
        closeCodeMirrorWidgetMenus();
        const textarea = document.getElementById(textareaId);
        const editor = textarea && textarea.codeMirrorEditor;

        if (action === 'find' || action === 'replace') {
            if (editor) {
                editor.execCommand(action);
            }
            return;
        }

        if (action === 'upload') {
            const uploadInput = document.getElementById(textareaId + '_upload');
            if (uploadInput) {
                uploadInput.click();
            }
            return;
        }

        if (action === 'save') {
            downloadCodeMirrorWidget(textareaId);
            return;
        }

        if (action === 'clear') {
            clearCodeMirrorWidget(textareaId);
            return;
        }

        if (action === 'paste') {
            pasteReplaceCodeMirrorWidget(textareaId);
            return;
        }

        if (action === 'copy') {
            copyCodeMirrorWidget(textareaId).catch(function() {
                alert('Unable to copy code right now. Please try again.');
            });
        }
    }

    function downloadCodeMirrorWidget(textareaId) {
        const textarea = document.getElementById(textareaId);
        if (!textarea) {
            return;
        }

        const code = textarea.codeMirrorEditor ? textarea.codeMirrorEditor.getValue() : textarea.value;
        const card = textarea.closest('[id^="' + QCODE_CARD_PREFIX + '"]');
        const baseName = (card && card.dataset.qcalcFunc ? card.dataset.qcalcFunc.trim() : '') || 'mycal';
        const language = normalizeCodeLanguage(textarea.dataset.lang || 'python');
        const fileSpec = codeFileSpec(language);
        const filename = baseName.replace(/[\\/:*?"<>|]/g, '_') + fileSpec.extension;
        const file = new Blob([code], { type: fileSpec.mime + ';charset=utf-8' });
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

    window.normalizeCodeLanguage = normalizeCodeLanguage;
    window.codeMirrorMode = codeMirrorMode;
    window.codeFileSpec = codeFileSpec;
    window.initializeCodeMirrorWidget = initializeCodeMirrorWidget;
    window.closeCodeMirrorWidgetMenus = closeCodeMirrorWidgetMenus;
    window.toggleCodeMirrorWidgetMenu = toggleCodeMirrorWidgetMenu;
    window.getCodeMirrorWidgetText = getCodeMirrorWidgetText;
    window.setCodeMirrorWidgetText = setCodeMirrorWidgetText;
    window.copyCodeMirrorWidget = copyCodeMirrorWidget;
    window.pasteReplaceCodeMirrorWidget = pasteReplaceCodeMirrorWidget;
    window.clearCodeMirrorWidget = clearCodeMirrorWidget;
    window.codeMirrorWidgetMenuAction = codeMirrorWidgetMenuAction;
    window.downloadCodeMirrorWidget = downloadCodeMirrorWidget;
    window.uploadCodeMirrorWidget = uploadCodeMirrorWidget;
})();
