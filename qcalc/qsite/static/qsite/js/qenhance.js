// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

/* qCalc post-render enhancements (markdown + tooltip enrichment) */

(function() {
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

    function qcalcInitHelpTooltips(root) {
        if (!(window.jQuery && window.jQuery.fn && window.jQuery.fn.tooltip)) {
            return;
        }

        var scope = root || document;
        var selector = '.qcalc-help-tip[data-toggle="tooltip"]';
        var nodes = [];

        if (scope && scope.matches && scope.matches(selector)) {
            nodes.push(scope);
        }
        if (scope && scope.querySelectorAll) {
            nodes = nodes.concat(Array.from(scope.querySelectorAll(selector)));
        }

        nodes.forEach(function(node) {
            var $node = $(node);
            if ($node.data('bs.tooltip')) {
                return;
            }
            $node.tooltip({
                container: 'body',
                boundary: 'window',
                template: '<div class="tooltip qcalc-help-tooltip" role="tooltip"><div class="arrow"></div><div class="tooltip-inner"></div></div>',
                html: true,
            });
        });
    }

    function runPostRenderEnhancements(root) {
        qcalcInitHelpTooltips(root);
        qmdEnhanceCodeBlocks(root);
        qmdEnhanceImages(root);
    }

    document.addEventListener('DOMContentLoaded', function() {
        runPostRenderEnhancements(document);
        if (document.body) {
            document.body.addEventListener('htmx:afterSwap', function() {
                runPostRenderEnhancements(document);
            });
        }
    });

    window.qmdCopyText = qmdCopyText;
    window.qmdEnhanceCodeBlocks = qmdEnhanceCodeBlocks;
    window.qmdEnhanceImages = qmdEnhanceImages;
    window.qcalcInitHelpTooltips = qcalcInitHelpTooltips;
    window.runPostRenderEnhancements = runPostRenderEnhancements;
})();
