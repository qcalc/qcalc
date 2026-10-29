// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

/*
 * qCalc common numeric slider.
 *
 * One floating slider, bound to the numeric input (or the value part of a
 * quantity) that currently has focus. Dragging writes the value into the input
 * and fires `input`; releasing fires one `change`, so whatever already listens
 * (interactive.js, showhide, autofill, anyof) behaves as if the user had typed.
 * Nothing here depends on interactive mode.
 *
 * Range: the input's own min/max if present, otherwise derived from the
 * current value and widened on release so the user can keep going.
 *
 * Opt-out per field (works through schema 'attrs'): data-qslider="off" on the
 * input or any ancestor. Optional: data-qslider-scale="log" for positive values
 * spanning orders of magnitude.
 *
 * Per calculator: the "slider_enabled" flag in the card's hidden extra_<cid>
 * field (initialised from the user preference 'slider', changed from the
 * calculator "..." menu through qcalc_ToggleSlider).
 */
(function() {
    if (window.__qcalc_SliderBootstrapped) {
        return;
    }
    window.__qcalc_SliderBootstrapped = true;

    var NUMERIC = ['val', 'val-p', 'val-pp', 'val-q', 'val-pq'];
    var SELECTOR = NUMERIC.map(function(c) { return 'input[type="number"].' + c; }).join(', ');
    var SKIP_ANCESTORS = '[data-qslider="off"], [data-interactive-ignore="true"], .tabulator';
    var FORM_PREFIX = 'form-';
    var EXTRA_PREFIX = 'extra_';
    var LOG_TICKS = 1000;

    var box = null;
    var rng = null;
    var loLabel = null;
    var hiLabel = null;
    var tip = null;
    var active = null;
    var cfg = null;
    var suspendedForm = null;
    var wasEnabled = false;

    function extraFor(cid) {
        var field = document.getElementById(EXTRA_PREFIX + cid);
        if (!field) {
            return null;
        }
        try {
            var obj = JSON.parse(field.value || '{}');
            return (obj && typeof obj === 'object') ? obj : {};
        } catch (_e) {
            return {};
        }
    }

    // The extra only carries a request level override. Without one, the effective value (user preference
    // or calculator default) is what the server rendered in the "..." menu item.
    function sliderEnabled(cid) {
        var extra = extraFor(cid);
        if (extra && (extra.slider_enabled === '0' || extra.slider_enabled === '1')) {
            return extra.slider_enabled === '1';
        }
        var item = document.getElementById('slider-' + cid);
        if (item) {
            return item.getAttribute('aria-checked') !== 'false';
        }
        return true;
    }

    function calculatorEnabled(el) {
        var form = el.form || el.closest('form');
        if (!form || form.id.indexOf(FORM_PREFIX) !== 0) {
            return true;
        }
        return sliderEnabled(form.id.slice(FORM_PREFIX.length));
    }

    function eligible(el) {
        return !!(el && el.matches && el.matches(SELECTOR)
            && !el.readOnly && !el.disabled
            && !el.closest(SKIP_ANCESTORS)
            && calculatorEnabled(el));
    }

    function build() {
        if (box) {
            return;
        }
        box = document.createElement('div');
        box.id = 'qcalc-slider';
        box.className = 'qcalc-slider';
        box.hidden = true;
        box.innerHTML = '<input type="range" aria-label="Adjust value">'
            + '<div class="qcalc-slider-ends"><span></span><output></output><span></span></div>';
        document.body.appendChild(box);
        rng = box.querySelector('input');
        var spans = box.querySelectorAll('.qcalc-slider-ends span');
        loLabel = spans[0];
        hiLabel = spans[1];
        tip = box.querySelector('output');
        wire();
    }

    function decimals(step) {
        var s = String(step);
        var e = s.indexOf('e-');
        if (e >= 0) {
            return parseInt(s.slice(e + 2), 10);
        }
        var dot = s.indexOf('.');
        return dot < 0 ? 0 : s.length - dot - 1;
    }

    function shortNum(n) {
        return String(Number(n.toPrecision(6)));
    }

    function rangeFor(el) {
        var v = parseFloat(el.value);
        if (isNaN(v)) {
            v = 0;
        }
        var min = el.min !== '' ? Number(el.min) : NaN;
        var max = el.max !== '' ? Number(el.max) : NaN;
        var fixedMax = !isNaN(max);
        var stepAttr = el.getAttribute('step');
        // Django IntegerField renders no step; FloatField renders step="any"
        var isInt = stepAttr === null;
        var authorStep = (stepAttr !== null && stepAttr !== 'any' && Number(stepAttr) > 0) ? Number(stepAttr) : 0;
        var log = el.dataset.qsliderScale === 'log' && v > 0 && isNaN(min) && isNaN(max);

        if (log) {
            min = v / 10;
            max = v * 10;
        } else {
            if (isNaN(min)) {
                min = v > 0 ? 0 : (v < 0 ? 2 * v : -10);
            }
            if (isNaN(max)) {
                max = v > 0 ? 2 * v : (v < 0 ? 0 : 10);
            }
        }
        if (max <= min) {
            max = min + 1;
        }
        var step = authorStep || (isInt ? 1 : Math.pow(10, Math.floor(Math.log10(max - min)) - 2));
        return {min: min, max: max, step: step, isInt: isInt, log: log, fixedMax: fixedMax};
    }

    function posFromValue(v) {
        if (!cfg.log) {
            return v;
        }
        v = Math.min(Math.max(v, cfg.min), cfg.max);
        return LOG_TICKS * Math.log(v / cfg.min) / Math.log(cfg.max / cfg.min);
    }

    function valueFromPos(p) {
        if (!cfg.log) {
            return Number(p);
        }
        return Number((cfg.min * Math.pow(cfg.max / cfg.min, p / LOG_TICKS)).toPrecision(4));
    }

    function formatValue(v) {
        if (cfg.isInt) {
            return String(Math.round(v));
        }
        if (cfg.log) {
            return String(v);
        }
        return String(Number(v.toFixed(decimals(cfg.step))));
    }

    function applyRange() {
        if (cfg.log) {
            rng.min = 0;
            rng.max = LOG_TICKS;
            rng.step = 1;
        } else {
            rng.min = cfg.min;
            rng.max = cfg.max;
            rng.step = cfg.step;
        }
        loLabel.textContent = shortNum(cfg.min);
        hiLabel.textContent = shortNum(cfg.max);
    }

    function place() {
        if (!active || !box) {
            return;
        }
        if (!document.documentElement.contains(active)) {
            unbind();
            return;
        }
        var r = active.getBoundingClientRect();
        if (r.bottom < 0 || r.top > window.innerHeight) {
            box.style.visibility = 'hidden';
            return;
        }
        var width = Math.max(r.width, 160);
        var height = box.offsetHeight || 48;
        var top = r.bottom + 2;
        if (top + height > window.innerHeight && r.top - height - 2 > 0) {
            top = r.top - height - 2;
        }
        box.style.left = Math.max(0, Math.min(r.left, window.innerWidth - width - 4)) + 'px';
        box.style.top = top + 'px';
        box.style.width = width + 'px';
        box.style.visibility = 'visible';
    }

    function bind(el) {
        build();
        active = el;
        cfg = rangeFor(el);
        applyRange();
        var v = parseFloat(el.value);
        rng.value = posFromValue(isNaN(v) ? cfg.min : v);
        tip.textContent = el.value;
        var cs = window.getComputedStyle(el);
        box.style.background = cs.backgroundColor;
        box.style.color = cs.color;
        box.hidden = false;
        place();
    }

    function unbind() {
        resume();
        if (box) {
            box.hidden = true;
        }
        active = null;
        cfg = null;
    }

    // Pressing the slider moves focus off the number input, and that focusout
    // (value already changed by the first drag step) would make interactive.js
    // schedule a calculation mid-drag. Suspend it for the drag, restore after.
    function suspend() {
        var form = active && active.form;
        if (!form || suspendedForm || !form.qcalcSuspendInteractive) {
            return;
        }
        suspendedForm = form;
        wasEnabled = form.dataset.interactiveEnabled === 'true';
        form.qcalcSuspendInteractive();
    }

    function resume() {
        if (!suspendedForm) {
            return;
        }
        var form = suspendedForm;
        suspendedForm = null;
        if (wasEnabled && form.qcalcResumeInteractive) {
            form.qcalcResumeInteractive();
        }
    }

    function wire() {
        rng.addEventListener('pointerdown', suspend);
        ['pointerup', 'pointercancel'].forEach(function(type) {
            rng.addEventListener(type, function() {
                window.setTimeout(resume, 0);  // after the change handler below
            });
        });

        rng.addEventListener('input', function() {
            if (!active || !document.documentElement.contains(active)) {
                unbind();
                return;
            }
            var text = formatValue(valueFromPos(rng.value));
            active.value = text;
            tip.textContent = text;
            active.dispatchEvent(new Event('input', {bubbles: true}));
        });

        rng.addEventListener('change', function() {
            if (!active) {
                return;
            }
            resume();
            active.dispatchEvent(new Event('change', {bubbles: true}));
            var v = parseFloat(active.value);
            var widened = false;
            if (cfg.log) {
                if (v >= cfg.max * 0.999) {
                    cfg.max *= 10;
                    widened = true;
                } else if (v <= cfg.min * 1.001) {
                    cfg.min /= 10;
                    widened = true;
                }
            } else if (!cfg.fixedMax && v >= cfg.max - cfg.step) {
                cfg.max = cfg.max * 2;
                widened = true;
            }
            if (widened) {
                applyRange();
                rng.value = posFromValue(v);
                hiLabel.textContent = shortNum(cfg.max);
            }
        });
    }

    document.addEventListener('focusin', function(event) {
        var target = event.target;
        if (eligible(target)) {
            bind(target);
        } else if (box && !box.contains(target)) {
            unbind();
        }
    });

    // a click on the already-focused input (e.g. after Esc) raises no focusin
    document.addEventListener('click', function(event) {
        if (event.target !== active && eligible(event.target)) {
            bind(event.target);
        }
    });

    // clicking blank page area does not move focus, so close on outside press
    document.addEventListener('pointerdown', function(event) {
        if (active && box && !box.contains(event.target) && event.target !== active) {
            unbind();
        }
    }, true);

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && active) {
            var el = active;
            unbind();
            el.focus();
        }
    });

    // typing or the native spinner re-derives the range from the new value
    document.addEventListener('change', function(event) {
        if (event.isTrusted && active && event.target === active) {
            bind(active);
        }
    });

    window.addEventListener('resize', place);
    document.addEventListener('scroll', place, true);
    document.addEventListener('htmx:afterSwap', function() {
        if (active && !document.documentElement.contains(active)) {
            unbind();
        }
    });

    // "..." menu item: flips this calculator's flag, persisted in its extra field
    window.qcalc_ToggleSlider = function(item, cid) {
        var on = !sliderEnabled(cid);
        if (window.QCalcActions && window.QCalcActions.updateExtra) {
            window.QCalcActions.updateExtra(cid, {slider_enabled: on ? '1' : '0'});
        }
        if (item) {
            item.setAttribute('aria-checked', on ? 'true' : 'false');
            var icon = item.querySelector('i');
            if (icon) {
                icon.classList.toggle('icon-checkbox-checked2', on);
                icon.classList.toggle('icon-checkbox-unchecked2', !on);
            }
        }
        if (!on && active && active.form && active.form.id === FORM_PREFIX + cid) {
            unbind();
        }
    };
})();
