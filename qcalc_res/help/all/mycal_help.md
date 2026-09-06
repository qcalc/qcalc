# Create My Calculator

## Purpose

Use **Create My Calculator** to turn your own qCalc calculation code into a
named calculator that you can save, open, and reuse. A saved calculator appears
in your personal qCalc catalog and can be used like other qCalc calculators.

This tool is best when you have a calculation you want to keep, rather than a
one-off expression. For a single multi-step calculation, use the **Simple
Expression Evaluator** `eva` instead.

## Create a Calculator

Enter a calculator name and its code. Your code needs two functions with the
same name:

- The calculator function performs the calculation.
- The `__info()` function provides the calculator title shown to users.

For a calculator named `addlen`, use this basic structure:

```text
def addlen(x='7 ft', y='8 m'):
    return Qty(x) + Qty(y)

def addlen__info():
    return {
        'title': 'Add Two Lengths'
    }
```

The function name and the calculator name must match. Input values with
defaults, such as `x='7 ft'`, let qCalc show a starting value and allow the
**Validate Input** check to run the calculator.

You can leave the calculator name field (`Cal Name`) blank when saving. In that case, qCalc uses the name of the calculator function it finds in your codebase.

## Code Controls

### Format Code

Formats the code and adds a basic matching `__info()` function when one is
missing. Check and adjust the generated title before saving.

### Check Syntax

Checks whether qCalc can read and run the code. Use this after making changes
and before saving.

### Validate Input

Runs each calculator function using its default input values. Every input that
is needed for validation must have a default value. The result identifies the
functions that passed validation or explains the problem that needs correcting.

### Save

Saves the code as your calculator. Saving a calculator with the same name
updates that saved calculator. The result includes an **Open** link so you can
open and use the calculator immediately.

### Load Code

Enter the name of one of your saved calculators, then select **Load Code** to
place its current code in the editor.

### Delete Code

Enter the name of one of your saved calculators, then select **Delete Code**
to remove it from your personal calculator catalog.

### My Catalog

Select **My Catalog** to browse your saved calculators.

## Results

After saving, **Remarks** lists the functions qCalc found and confirms the name
used to run the calculator. The **Open** result opens the saved calculator.

## Note

qCalc only saves code that it can validate. Make sure the calculator function
and its matching `__info()` function use the same name, for example `addlen()`
and `addlen__info()`.

Changing code in the editor does not change an existing saved calculator until
you select **Save**. Deleting code removes the saved calculator, so use it only
when you no longer need that calculator.