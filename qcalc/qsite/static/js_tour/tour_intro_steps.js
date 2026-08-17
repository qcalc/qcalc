// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

const introSteps = [
  {
    title: "Introduction Tour",
    element: '#intro-tour',
    intro: "Welcome to qCalc! Let's walk through some of it's features.",
    position: 'bottom',
    container: ''
  },
  {
    title: "Sidebar: Home",
    element: '#nav-home',
    intro: 'Navigate to the Home page. From the Home page, you can access the calculator and quantity catalogs.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Topbar: Home",
    element: '#head-home',
    intro: 'You can also navigate to the Home page at any time by clicking here.',
    position: 'bottom',
    container: 'pagetop'
  },
  {
    title: "Primary Navigation",
    element: '#nav-side-main',
    intro: 'Access the main navigation menu (toggle on/off). [click] on the icon to try it!',
    position: 'bottom',
    container: 'navbar',
    disableInteraction: false,
  },
  {
    title: "Secondary Navigation",
    element: '#nav-side-secondary',
    intro: 'Access the secondary navigation menu (toggle on/off). You can add calculators and search units from here. [click] on the icon to try it!',
    position: 'bottom',
    container: 'navbar',
    disableInteraction: false,
  },
  {
    title: "Calculator Catalog",
    element: '#nav-calc-tree',
    intro: 'Explore the Calculator catalog in a tree-structured format.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Quantity Catalog",
    element: '#nav-qty-tree',
    intro: 'Delve into the Quantity catalog presented in a tree-structured format.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Catalog Search",
    element: '#search-catalog',
    intro: 'Search through the qCalc catalog to find calculators and units.',
    position: 'bottom',
    container: 'pagetop'
  },
  {
    title: "Add Calculator",
    element: '#nav-add-calc',
    intro: 'Add a calculator to the screen and perform calculations by entering the full or partial name of the calculator.',
    position: 'top',
    container: 'sidebar2'
  },
  {
    title: "Search Unit",
    element: '#nav-search-unit',
    intro: 'Search for units of measurement to assist in selecting from the list of UOMs on the calculator form.',
    position: 'right',
    container: 'sidebar2'
  },
  {
    title: "Load File",
    element: '#open-io-file',
    intro: 'Load a saved calculator input file on your computer.',
    position: 'right',
    container: 'sidebar2'
  },
  {
    title: "Open File",
    element: '#load-io',
    intro: 'Open the calculator with input from the loaded file.',
    position: 'right',
    container: 'sidebar2'
  },
  {
    title: "Unit Converter",
    element: '#nav-conv',
    intro: 'Open a Unit Conversion calculator.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Quick Calculator",
    element: '#nav-cal',
    intro: 'Open a traditional calculator.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Currency Converter",
    element: '#nav-cur',
    intro: 'Open a Currency converter.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Expression Evaluator",
    element: '#nav-eva',
    intro: 'Evaluate ad hoc mathematical expressions.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Console",
    element: '#nav-console',
    intro: 'Open the console for advanced operations.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Your Prefernces",
    element: '#nav-pref',
    intro: 'Customize your qCalc preferences, including decimal formats, themes, and charting options.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Your Account",
    element: '#nav-user',
    intro: 'Utilize the user menu to log in and access your saved items.',
    position: 'left',
    container: 'navbar'
  },
  {
    title: "Clear Screen",
    element: '#nav-clear',
    intro: 'Remove calculators from the screen and reset the browser page.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Create Calculator",
    element: '#nav-mycal',
    intro: 'Create your own calculator using python within qCalc.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Personal Catalog",
    element: '#nav-ucalc-tree',
    intro: 'Access the catalog of your own calculators in a tree-structured format.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Public Catalog",
    element: '#nav-pcalc-tree',
    intro: 'Explore calculators made public by other users.',
    position: 'right',
    container: 'sidebar'
  },
  {
    title: "Introduction Tour Ends",
    element: '#intro-tour',
    intro: 'Thank you for taking the quick introduction tour. Hope you found it useful.',
    position: 'bottom',
    container: ''
  }
];

function intro_onbeforechange(targetElement) {
  ;
}

function intro_onchange(targetElement) {
  ;
}

function introTour() {
  startTour(introSteps, intro_onbeforechange, intro_onchange);
}
