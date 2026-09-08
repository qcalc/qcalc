// qCalc live form interaction
(function() {
    function updateInteractiveButton(button, enabled) {
        var icon = button.querySelector('i');
        if (icon) {
            icon.classList.toggle('icon-switch', enabled);
            icon.classList.toggle('icon-switch22', !enabled);
        }
        button.setAttribute('aria-pressed', enabled ? 'true' : 'false');
        button.classList.toggle('active', enabled);
    }

    function updateInteractiveTarget(form, enabled) {
        var cid = form.id.replace('form-', '');
        form.setAttribute('data-interactive', 'true');
        form.setAttribute('hx-sync', 'this:replace');
        form.setAttribute('hx-target', '#output-part-' + cid);
        form.setAttribute('hx-swap', 'outerHTML');
        if (window.htmx) {
            htmx.process(form);
        }
    }

    window.qcalc_ToggleInteractive = function(button) {
        var form = button ? button.closest('form') : null;
        if (!form) {
            return;
        }

        var enabled = form.dataset.interactiveEnabled !== 'true';
        form.dataset.interactiveEnabled = enabled ? 'true' : 'false';
        updateInteractiveTarget(form, enabled);
        updateInteractiveButton(button, enabled);
        if (window.updateExtra) {
            updateExtra(form.id.replace('form-', ''), {
                interactive_enabled: enabled ? '1' : '0'
            });
        }

        if (!enabled && form.qcalcCancelInteractive) {
            form.qcalcCancelInteractive();
        }
    };

    function resolveForm(formOrElemOrCid) {
        if (typeof formOrElemOrCid === 'string') {
            return document.getElementById('form-' + formOrElemOrCid);
        }
        if (formOrElemOrCid && formOrElemOrCid.tagName === 'FORM') {
            return formOrElemOrCid;
        }
        return null;
    }

    window.qcalc_InitInteractive = function(formOrElemOrCid) {
        var form = resolveForm(formOrElemOrCid);
        if (!form || form.dataset.interactive !== 'true'
            || form.dataset.interactiveInitialized === '1') {
            return;
        }

        form.dataset.interactiveInitialized = '1';
        var toggleButton = form.querySelector('[id^="interactive-"]');
        var interactiveEnabled = !toggleButton
            || toggleButton.getAttribute('aria-pressed') !== 'false';
        form.dataset.interactiveEnabled = interactiveEnabled ? 'true' : 'false';
        if (toggleButton) {
            updateInteractiveButton(toggleButton, interactiveEnabled);
        }
        var timer = null;

        function isInputTableEvent(event) {
            var target = event.target;
            return target.closest(
                'table.table-in, .table-responsive.table-in, '
                + '[data-interactive-ignore="true"], .tabulator, '
                + '.tabulator-cell, .tabulator-editor, .tabulator-popup-container'
            ) !== null;
        }

        function cancelPendingCalculation() {
            clearTimeout(timer);
            timer = null;
        }

        form.qcalcSuspendInteractive = function() {
            cancelPendingCalculation();
            form.dataset.interactiveEnabled = 'false';
        };

        function isSelect2Control(target) {
            return target.matches('select.select2-hidden-accessible, select.select2');
        }

        function isTextLikeControl(target) {
            if (target.matches('textarea')) {
                return true;
            }
            if (!target.matches('input:not([type="hidden"])')) {
                return false;
            }
            return !target.matches(
                '[type="button"], [type="checkbox"], [type="file"], '
                + '[type="image"], [type="radio"], [type="range"], '
                + '[type="reset"], [type="submit"]'
            );
        }

        function controlValue(control) {
            if (control.matches('select[multiple]')) {
                return Array.from(control.selectedOptions).map(function(option) {
                    return option.value;
                }).join('\u001f');
            }
            return control.value;
        }

        function scheduleCalculation() {
            if (form.dataset.interactiveEnabled !== 'true') {
                return;
            }
            clearTimeout(timer);
            timer = setTimeout(function() {
                var calculateButton = form.querySelector('button[type="submit"]');
                if (calculateButton && !calculateButton.disabled) {
                    calculateButton.click();
                }
            }, 300);
        }

        form.qcalcCancelInteractive = cancelPendingCalculation;

        form.addEventListener('focusout', function(event) {
            if (isInputTableEvent(event)) {
                cancelPendingCalculation();
            } else if (isTextLikeControl(event.target)
                && event.target.dataset.interactiveInitialValue !== controlValue(event.target)) {
                scheduleCalculation();
            }
        });
        form.addEventListener('change', function(event) {
            if (isInputTableEvent(event)) {
                cancelPendingCalculation();
            } else if (!isSelect2Control(event.target)
                && event.target.matches('input:not([type="hidden"]), select')) {
                scheduleCalculation();
            }
        });
        form.addEventListener('focusin', function(event) {
            if (isInputTableEvent(event)) {
                cancelPendingCalculation();
            } else if (isTextLikeControl(event.target)) {
                event.target.dataset.interactiveInitialValue = controlValue(event.target);
            }
        });

        if (window.jQuery) {
            $(form).on(
                'select2:select.qcalcInteractive '
                + 'select2:clear.qcalcInteractive select2:unselect.qcalcInteractive',
                'select',
                function(event) {
                    if (!isInputTableEvent(event)) {
                        scheduleCalculation();
                    }
                }
            );
        }
    };

    function initInteractiveForms(root) {
        var scope = root || document;
        var forms = scope.querySelectorAll
            ? scope.querySelectorAll('form[data-interactive="true"]') : [];
        forms.forEach(window.qcalc_InitInteractive);
        if (scope.matches && scope.matches('form[data-interactive="true"]')) {
            window.qcalc_InitInteractive(scope);
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        initInteractiveForms(document);
    });

    document.body.addEventListener('htmx:afterSwap', function(event) {
        initInteractiveForms(event.detail && event.detail.target);
    });
})();
