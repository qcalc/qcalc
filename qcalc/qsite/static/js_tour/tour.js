// Custom alert function using Tingle.js
function customAlert(message, title = 'Alert', callback = null) {
    // Create a new Tingle modal instance
    const modal = new tingle.modal({
        footer: true,
        closeMethods: ['overlay', 'escape'],
        closeLabel: "",
        onClose: function() {
            if (callback) callback(); // Call the callback if provided
        }
    });

    // Set the modal content
    modal.setContent(`
      <div class="modal-title-bar">
        <h2>${title}</h2>
      </div>
      <div class="modal-message">
        <p>${message}</p>
      </div>
    `);

    // Add a footer button
    modal.addFooterBtn('OK', 'tingle-btn tingle-btn--primary', function() {
        modal.close(); // Close the modal
    });

    // Open the modal
    modal.open();
}

function isMobile() {
  return window.matchMedia('(max-width: 768px)').matches;
}

function isMobileVisible(classList) {
  return classList.contains('d-md-block') && !classList.contains('d-none');
}

function isDesktopVisible(classList) {
  return classList.contains('d-md-none') && !classList.contains('d-none');
}

function expandSidebar(expand) {
  const sidebar = document.querySelector("#sidebar-main");
  let btnSidebar;

  if (isMobile()) {
    btnSidebar = document.querySelector("#mob-side-main");
  } else {
    btnSidebar = document.querySelector("#nav-side-main");
  }

  if (expand && sidebar.clientWidth < 100) {
    btnSidebar.click();
  } else if (!expand && sidebar.clientWidth > 100) {
    btnSidebar.click();
  }
}

function expandSidebar2(expand) {
  const sidebar2 = document.querySelector("#sidebar-secondary");
  let btnSidebar2;

  if (isMobile()) {
    btnSidebar2 = document.querySelector("#mob-side-secondary");
  } else {
    btnSidebar2 = document.querySelector("#nav-side-secondary");
  }

  if (expand && sidebar2.clientWidth < 100) {
    btnSidebar2.click();
  } else if (!expand && sidebar2.clientWidth > 100) {
    btnSidebar2.click();
  }
}

function isElementVisible(selector) {
  const el = document.querySelector(selector);
  if (!el) return false; // Check if el is a DOM element
  return true;
  /*const rect = el.getBoundingClientRect();
  const windowHeight = (window.innerHeight || document.documentElement.clientHeight);
  const windowWidth = (window.innerWidth || document.documentElement.clientWidth);

  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= windowHeight &&
    rect.right <= windowWidth
  );*/
}

function clickElement(selector) {
  const element = document.querySelector(selector);
  if (element) {
    element.click();
  }
}

const intro = introJs();

// modify steps which is an array of dict
// with the supplied updates which is a dict
// the step is identified by title
function modifyStep(title, updates) {
  steps = intro._options.steps;
  currentStep = intro._currentStep
  for (let i = 0; i < steps.length; i++) {
    if (steps[i].title === title) {
      Object.assign(steps[i], updates);
      //intro.setOptions({steps: steps});
      intro._options.steps = steps;
      intro.start();
      break;
    }
  }
}

function startTour(allSteps, callback_onbeforechange, callback_onchange) {
  if (isMobile()) {
    customAlert('Tour is not suitable for a screen width less than 768px. Please switch to landscape mode and try again.');
    return;
  }

  // Filter out steps where the element is not visible
  const validSteps = allSteps.filter(step => step.element && (step.type === 'dynamic' || isElementVisible(step.element)));
  if (validSteps.length === 0) {
    customAlert('No steps to show. Please resize your browser or ensure the sidebar is visible.');
    return;
  }

 // Initialize Intro.js with valid steps
  intro.setOptions({
    steps: validSteps,
    showProgress: true,
    showBullets: false,
    nextLabel: 'Next',
    prevLabel: 'Back',
    autoPosition: true,
    showStepNumbers: true,
    scrollToElement: true,
    doneLabel: 'Done',
    disableInteraction: true,
  });

  intro.onbeforechange(function (targetElement) {
    //console.log(targetElement.id);
    const currentStepIndex = intro.currentStep();
    const currentStep = intro._options.steps[currentStepIndex];
    if (currentStep.container=='sidebar' || currentStep.title=='Primary Navigation') {
      expandSidebar2(false);
      expandSidebar(true);
    } else if (currentStep.container=='sidebar2' || currentStep.title=='Secondary Navigation') {
      expandSidebar(false);
      expandSidebar2(true);
    } else {
      expandSidebar(false);
      expandSidebar2(true);
    }
    callback_onbeforechange(targetElement);
  });

  intro.onchange(function (targetElement) {
    callback_onchange(targetElement);
  });

  intro.start();

  // Access currentStep after starting
  setTimeout(() => {
    ;
    //console.log("Current step index (after start):", intro.currentStep()); // Should now be valid
  }, 100);

}

