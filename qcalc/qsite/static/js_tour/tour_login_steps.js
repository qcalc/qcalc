// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

const loginSteps = [
  {
    title: "My Account Tour",
    element: '#login-tour',
    intro: "Let's walk through the steps to learn what your user account has to offer.",
    position: 'bottom',
    container: ''
  },
  {
    title: "Account Tour Ends",
    element: '#login-tour',
    intro: 'Thank you for taking the account tour. Hope you found it useful.',
    position: 'bottom',
    container: ''
  }
]

function login_onbeforechange(targetElement) {
  ;
}
function login_onchange(targetElement) {
  ;
}

function loginTour() {
  startTour(loginSteps, login_onbeforechange, login_onchange);
}
