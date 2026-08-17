// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

var calcSteps = [
  {
    title: "Calculation Tour",
    element: '#calc-tour',
    intro: "Let's walk through the steps to learn how to use a qCalc calculator.",
    position: 'bottom',
    container: ''
  },
  {
    title: "Add Calculator: Input Name",
    element: '#fname_sb',
    intro: 'We will type "bmi" as the calculator name and perform body mass index calculations.',
    position: 'top',
    container: 'sidebar2',
  },
  {
    title: "Add Calculator: Enter",
    element: '#btn_fname_sb',
    intro: '[Click] on the button (+) to open the Calculator',
    position: 'top',
    container: 'sidebar2',
    disableInteraction: false,
  },
  {
    title: "Calculate",
    element: '.btncal',
    intro: '[Click] on the [Calculate] button to execute',
    position: 'top',
    container: 'sidebar2',
    disableInteraction: false,
    type: 'dynamic',
  },
  {
    title: "Calculation Tour Ends",
    element: '#calc-tour',
    intro: 'Thank you for taking the calculation tour. Hope you found it useful.',
    position: 'bottom',
    container: ''
  },
]
function calc_onbeforechange(targetElement) {
  if (targetElement.id==='fname_sb') {
    targetElement.value = "bmi";
    //targetElement.focus();
  }
  if (targetElement.id==='btn_fname_sb') {
    ;
  }
}

function calc_onchange(targetElement) {
  if (targetElement.id==='btn_fname_sb') {
    document.querySelector('#btn_fname_sb').click();
    /*setTimeout(() => {
        cid = getCid();
        updates = {element: '#calculate_'+cid}
        console.log(updates);
        modifyStep("Calculate", updates)
    }, 1000);*/
  }
}

function calcTour() {
  startTour(calcSteps, calc_onbeforechange, calc_onchange);
}
