// SPDX-License-Identifier: MIT
// Copyright (c) 2024-2026 Debasish C Saha

(function() {
    const commandHistory = [];
    let historyIndex = -1;

    const qconsole = document.getElementById('qconsole');
    let commandLine = createCommandLine();

    function createCommandLine() {
        const commandLine = document.createElement('div');
        commandLine.className = 'command-line';

        const prompt = document.createElement('span');
        prompt.className = 'prompt';
        prompt.innerHTML = '&gt;&gt;&nbsp;';

        const command = document.createElement('span');
        command.className = 'command';
        command.contentEditable = 'true';

        commandLine.appendChild(prompt);
        commandLine.appendChild(command);
        qconsole.appendChild(commandLine);
        command.focus();

        return commandLine;
    }  // createCommandLine()

    function appendNewCommandLine() {
        return createCommandLine();
    }  // appendNewCommandLine()

    function processCommand(command) {
        command = command.trim()
        if (command !== '') {
            commandHistory.push(command);
            historyIndex = commandHistory.length;
        }
        if ( command === 'cls' || command === 'clear') {
            qconsole.innerHTML = '';
            commandLine = appendNewCommandLine();
        } else {
            fetch('/page/console/execute/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                const responseLine = document.createElement('div');
                responseLine.style.whiteSpace = 'pre-wrap';
                responseLine.textContent = data.response;
                qconsole.insertBefore(responseLine, commandLine.nextSibling);
                commandLine = appendNewCommandLine();
                qconsole.scrollTop = qconsole.scrollHeight;
            });
        }
    }  // processCommand()


    function handleKeyDown(event) {
        const key = event.key;
        const commandElement = commandLine.querySelector('.command');
//        console.log(commandLine)
        if (key === 'Enter') {
            event.preventDefault(); // Prevent default behavior
            const command = commandElement.textContent;
            commandElement.contentEditable = 'false'; // Disable editing of the previous command
            processCommand(command);
        } else if (key === 'Backspace') {
            if (commandElement.textContent.length === 0) {
                event.preventDefault(); // Prevent backspace if the command part is empty
            }
        } else if (key === 'ArrowUp') {
            event.preventDefault();
            if (historyIndex > 0) {
                historyIndex--;
                commandElement.textContent = commandHistory[historyIndex];
                placeCursorAtEnd(commandElement);
            }
        } else if (key === 'ArrowDown') {
            event.preventDefault();
            if (historyIndex < commandHistory.length - 1) {
                historyIndex++;
                commandElement.textContent = commandHistory[historyIndex];
            } else {
                historyIndex = commandHistory.length;
                commandElement.textContent = '';
            }
            placeCursorAtEnd(commandElement);
        }
    } // handleKeyDown()

    qconsole.addEventListener('keydown', handleKeyDown)

    qconsole.addEventListener('click', (event) => {
        const clickedElement = event.target;
        const commandElement = commandLine.querySelector('.command');
        if (commandElement.contains(clickedElement)) {
            commandElement.focus();
        }
    });

    qconsole.addEventListener('dblclick', (event) => {
        const commandElement = commandLine.querySelector('.command');
        commandElement.focus();
        placeCursorAtEnd(commandElement);
    });

    // Force plain-text paste in the console command input
    qconsole.addEventListener('paste', (event) => {
    const commandElement = commandLine.querySelector('.command');

    // Only handle paste when current editable command is the target
    if (!commandElement || event.target !== commandElement) {
        return;
    }

    event.preventDefault();

    const text = (event.clipboardData || window.clipboardData).getData('text/plain') || '';

    // Preferred path for contenteditable
    if (document.queryCommandSupported && document.queryCommandSupported('insertText')) {
        document.execCommand('insertText', false, text);
        return;
    }

    // Fallback path
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) {
        commandElement.textContent += text;
        return;
    }

    sel.deleteFromDocument();
    sel.getRangeAt(0).insertNode(document.createTextNode(text));
    sel.collapseToEnd();
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }  // getCookie()

    function placeCursorAtEnd(element) {
        const range = document.createRange();
        const selection = window.getSelection();
        range.selectNodeContents(element);
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
    }  // placeCursorAtEnd()

})();

