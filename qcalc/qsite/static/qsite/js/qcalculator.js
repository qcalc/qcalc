// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

$(document).ready(function() {
  let currentOperand = '';
  let decimalAllowed = true;
  let computed = false;
  let maxlen = 255;
  prevOperand = '';

  function clearDisplay() {
    currentOperand = '';
    decimalAllowed = true;
    updateDisplay();
  }

  function appendNumber(number) {
    if (computed) { clearDisplay();  }
    if (currentOperand === '0' || currentOperand === 'Error') currentOperand = '';
    if (!(decimalAllowed === false && number === '.')) {
      currentOperand += number;
      if (number === '.') decimalAllowed = false;
    }
    updateDisplay();
  }

  function chooseOp(op) {
    if (op === '+' || op === '-'){
      currentOperand += ` ${op} `;
    } else {
      currentOperand += op;
    }
    updateDisplay();
    decimalAllowed = true;
  }

  function preprocess_xpr(xpr) {
    xpr = xpr.replace(/\^/g, '**');
    xpr = xpr.replace(/\*\*\*\*/g, '^');
    return xpr.replace(/\|/g,''); //.replace(/\!/g,'/')
  }

  function compute() {
    try {
      prevOperand = currentOperand;
      const result = eval(preprocess_xpr(currentOperand)); // Replace with a safe evaluation method
      currentOperand = result.toString();
    } catch (error) {
      currentOperand = "Error";
    }
    updateDisplay();
    computed = true;
  }

  function reverse() {
    currentOperand = '1/('+currentOperand+')';
    compute();
  }

  function copyClip() {
    const result = currentOperand.toString();
    if (navigator.clipboard && result) {
      // Check if clipboard API is available and there is a result to copy
      navigator.clipboard.writeText(result).then(() => {
        console.log('Result copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy: ', err);
      });
    } else {
      console.error('Clipboard API not available or invalid result');
    }
  }

  function deleteEntry() {
    currentOperand = currentOperand.slice(0, -1);
    updateDisplay();
  }

  function updateDisplay() {
    const display = document.getElementById('display');
    text = currentOperand || '0';
    if(text.length <= maxlen){
      display.innerText = text;
    } else {
      display.innerText = text.substring(0, maxlen)+'|';
    }
    computed = false;
  }

  function prevEntry(){
     temp = currentOperand;
     currentOperand = prevOperand;
     prevOperand = temp;
     updateDisplay();
  }

  document.querySelectorAll('.button').forEach(button => {
    button.addEventListener('click', () => {
      const { action, value } = button.dataset;
      if (action === 'add') appendNumber(value);
      else if (action === 'operate') chooseOp(value);
      else if (action === 'compute') compute();
      else if (action === 'reverse') reverse();
      else if (action === 'clear') clearDisplay();
      else if (action === 'del') deleteEntry();
      else if (action === 'copy') copyClip();
      else if (action === 'prev') prevEntry();
    });
  });

  const calculator = document.querySelector('.calculator');
  calculator.focus();
  calculator.addEventListener('keydown', (e) => {
    if ((e.key >= '0' && e.key <= '9') || e.key === '.' || e.key === '+/-') appendNumber(e.key);
    else if (['/', '*', '-', '+', '(', ')', '^'].includes(e.key)) chooseOp(e.key);
    if (e.key === 'Enter') compute();
    else if (e.key === 'Escape') clearDisplay();
    else if (e.key === 'Backspace') deleteEntry();
    e.preventDefault(); // Prevent default to avoid any unwanted behavior
  });

  clearDisplay(); // Initialize display
});