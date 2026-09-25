# qCalc Interactivity Guide (End User)

## Purpose
Interactive mode lets a calculator run automatically after input changes, so you do not need to press Calculate every time.

## Before You Start
- Interactive works only when both are true:
- Your user preference for interactive mode is ON.
- The specific calculator supports interactive mode.
- If either is off, behavior is manual (press Calculate).

## How Interactive Triggers
- Typing in text-like inputs triggers a calculation after you leave the field, only if the value changed.
- Changing standard input or select fields triggers a calculation.
- Select2 field selections and clears also trigger a calculation.
- A short debounce delay is used so multiple quick edits become one calculation.

## What Does Not Trigger Automatically
- Hidden fields.
- Controls marked to be ignored for interactive flow.
- Some table operations that need structural updates (see Table section below).

## Table Input Behavior
- Clicking Update in a table keeps interactive mode working.
- The app briefly pauses interactive while syncing table data.
- After sync, interactive mode is restored if it was enabled before Update.
- One Calculate action then runs automatically to refresh output.
- Resize and Edit/Display doesn't trigger interactivity.

## Useful Habits
- Use Update after changing table cells to ensure table payload is saved.
- If output seems stale, press Calculate once to confirm state.
- For large inputs, pause briefly after edits to let the debounce submit complete.

## Troubleshooting Checklist
- Confirm your interactive preference is ON.
- Confirm the calculator actually supports interactive mode. You will see a button with record icon when a calculator supports interactive mode.
- Check that you changed a value (no change means no trigger for text-like inputs).
- If using table input, click Update after edits.

## Performance Notes
- Interactive can produce frequent submissions on heavy calculators.
- For long-running calculations, manual Calculate may feel better.

## Accessibility Notes
- The interactive toggle uses pressed-state semantics.
- If needed, keep interactive OFF and use manual Calculate for predictable step-by-step control.
