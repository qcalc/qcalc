# qCalc Code Editor Guide
<!-- TOC -->
* [qCalc Code Editor Guide](#qcalc-code-editor-guide)
  * [1. Where you use the editor](#1-where-you-use-the-editor)
  * [2. Writing calculator code in `mycal`](#2-writing-calculator-code-in-mycal)
  * [3. Evaluating an expression in `eva`](#3-evaluating-an-expression-in-eva)
  * [4. Editor features](#4-editor-features)
  * [5. Keyboard shortcuts](#5-keyboard-shortcuts)
  * [6. File and fullscreen controls](#6-file-and-fullscreen-controls)
<!-- TOC -->

The qCalc code editor is used when you write Python code for a calculator in `mycal` or enter a Python expression in `eva`. It is a Python-aware editing surface designed to make code entry, correction, and reuse easier.

## 1. Where you use the editor

Use `mycal` to write a complete calculator function and its metadata function. Use `eva` when you want to evaluate a Python expression directly without creating and saving a calculator.

The editor does not replace qCalc's normal validation workflow. In `mycal`, use the available **Check Syntax**, **Format Code**, validation, and save actions after editing your code.

## 2. Writing calculator code in `mycal`

Create a calculator by defining a Python function and a matching `__info()` function. The main function contains the calculation; `__info()` supplies the calculator title and other form metadata.

```python
def circle_area(radius=1.0):
    return pi * radius ** 2


def circle_area__info():
    return {
        "title": "Circle Area",
    }
```

The indentation in the example is important: statements inside a Python function are indented by four spaces. Select several lines and press `Tab` to indent them together, or `Shift+Tab` to remove one indentation level.

## 3. Evaluating an expression in `eva`

Use `eva` for a quick calculation or to experiment with a qCalc expression. For example:

```python
Qty("10 m") + Qty("3 ft")
```

You can also enter a longer expression over several lines when it is clearer to do so. `eva` evaluates what you enter; it does not require a calculator function or an `__info()` function.

## 4. Editor features

- **Python syntax highlighting** distinguishes code elements visually.
- **Line numbers** make it easier to locate an error reported by a syntax check.
- **Bracket matching** highlights the matching parenthesis, square bracket, or brace near the cursor.
- **Auto-close brackets and quotes** adds the matching `)`, `]`, `}`, single quote, or double quote after you type an opening character. Type a closing character to move past an existing match. Press `Backspace` between an empty matching pair to remove both characters.
- **Four-space indentation** is used for `Tab`, which matches normal Python style.
- **Multiline indentation** applies `Tab` or `Shift+Tab` to every selected line.
- **Column-100 ruler** provides a subtle vertical guide for keeping lines readable.
- **Line wrapping** keeps long lines visible without requiring horizontal scrolling.
- **Browser context menu** remains available for familiar commands such as Copy, Paste, and Select All.

## 5. Keyboard shortcuts

| Key | Action |
| --- | --- |
| `Tab` | Insert four spaces at the cursor, or indent all selected lines. |
| `Shift+Tab` | Outdent the current line, or outdent all selected lines. |
| `Ctrl+S` (Windows/Linux) | Download the current editor contents as a Python file. |
| `Cmd+S` (macOS) | Download the current editor contents as a Python file. |
| `F11` | Toggle fullscreen editing for the current code editor. |

## 6. File and fullscreen controls

The buttons below the editor let you move code between qCalc and a local file:

- Use the **Upload from Python file** button to load a `.py` file into the editor.
- Use the **Save to Python file** button, or the `Ctrl+S`/`Cmd+S` shortcut, to download the current contents as a `.py` file.
- Use the small fullscreen control at the editor corner, or `F11`, to make the editor fill the screen. Use the same control or `F11` again to return to the normal view.

After changing code in `mycal`, run qCalc's syntax check and validation before saving the calculator.