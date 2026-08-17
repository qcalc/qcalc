/* SPDX-License-Identifier: MIT
   Copyright (c) 2024-2026 Debasish C Saha */

/* =============================================================================
   qcalc-layout/app.js
   Handles: sidebar toggles (desktop + mobile), header elements, dropdown submenus
   Requires: jQuery 3.3.1, Bootstrap 4.3.1
   ============================================================================= */

var App = (function () {

    /* -- Transition helpers ------------------------------------------------- */
    function _transitionsDisabled() { $('body').addClass('no-transitions'); }
    function _transitionsEnabled()  { $('body').removeClass('no-transitions'); }

    /* -- Desktop sidebar toggles ------------------------------------------- */

    /* .sidebar-main-toggle → collapse sidebar to icon-only (sidebar-xs) */
    function _sidebarMainResize() {
        $(document).on('click', '.sidebar-main-toggle', function (e) {
            e.preventDefault();
            $('body').toggleClass('sidebar-xs').removeClass('sidebar-mobile-main');
        });
    }

    /* .sidebar-main-hide → hide sidebar completely */
    function _sidebarMainToggle() {
        $(document).on('click', '.sidebar-main-hide', function (e) {
            e.preventDefault();
            $('body').toggleClass('sidebar-main-hidden');
        });
    }

    /* .sidebar-secondary-toggle → hide/show secondary sidebar */
    function _sidebarSecondaryToggle() {
        $(document).on('click', '.sidebar-secondary-toggle', function (e) {
            e.preventDefault();
            $('body').toggleClass('sidebar-secondary-hidden');
        });
    }

    /* -- Mobile sidebar toggles -------------------------------------------- */

    function _addBackdrop() {
        if ($('.sidebar-mobile-backdrop').length) return;
        $('<div class="sidebar-mobile-backdrop"></div>')
            .appendTo('body')
            .on('click', function () {
                $('body').removeClass('sidebar-mobile-main sidebar-mobile-secondary');
                $(this).remove();
            });
    }
    function _removeBackdrop() { $('.sidebar-mobile-backdrop').remove(); }

    function _sidebarMobileMainToggle() {
        $(document).on('click', '.sidebar-mobile-main-toggle', function (e) {
            e.preventDefault();
            var wasOpen = $('body').hasClass('sidebar-mobile-main');
            $('body').toggleClass('sidebar-mobile-main').removeClass('sidebar-mobile-secondary');
            wasOpen ? _removeBackdrop() : _addBackdrop();
        });
    }

    function _sidebarMobileSecondaryToggle() {
        $(document).on('click', '.sidebar-mobile-secondary-toggle', function (e) {
            e.preventDefault();
            var wasOpen = $('body').hasClass('sidebar-mobile-secondary');
            $('body').toggleClass('sidebar-mobile-secondary').removeClass('sidebar-mobile-main');
            wasOpen ? _removeBackdrop() : _addBackdrop();
        });
    }

    /* .sidebar-mobile-expand → fullscreen sidebar on mobile */
    function _sidebarMobileFullscreen() {
        $(document).on('click', '.sidebar-mobile-expand', function (e) {
            e.preventDefault();
            $(this).closest('.sidebar').toggleClass('sidebar-fullscreen');
        });
    }

    /* -- Header element toggler -------------------------------------------- */
    function _headerElements() {
        $(document).on('click', '.header-elements-toggle', function (e) {
            e.preventDefault();
            /* exclude the toggle itself: its own class ("header-elements-toggle")
               also matches [class*=header-elements-], which would stop closest() early */
            $(this).closest('[class*=header-elements-]:not(.header-elements-toggle)').find('.header-elements').toggleClass('d-none');
        });
    }

    /* -- Dropdown submenus ------------------------------------------------- */
    function _dropdownSubmenu() {
        $(document).on('click', '.dropdown-menu .dropdown-submenu:not(.disabled) .dropdown-toggle', function (e) {
            e.stopPropagation();
            e.preventDefault();
            $(this).parent().siblings().removeClass('show').find('.show').removeClass('show');
            $(this).parent().toggleClass('show').children('.dropdown-menu').toggleClass('show');
            $(this).parents('.show').on('hidden.bs.dropdown', function () {
                $('.dropdown-submenu .show, .dropdown-submenu.show').removeClass('show');
            });
        });
    }

    /* -- Public API --------------------------------------------------------- */
    return {
        initBeforeLoad: function () { _transitionsDisabled(); },
        initAfterLoad:  function () { _transitionsEnabled(); },

        initCore: function () {
            _sidebarMainResize();
            _sidebarMainToggle();
            _sidebarSecondaryToggle();
            _sidebarMobileMainToggle();
            _sidebarMobileSecondaryToggle();
            _sidebarMobileFullscreen();
            _headerElements();
            _dropdownSubmenu();
        }
    };
}());

document.addEventListener('DOMContentLoaded', function () {
    App.initBeforeLoad();
    App.initCore();
});
window.addEventListener('load', function () {
    App.initAfterLoad();
});
