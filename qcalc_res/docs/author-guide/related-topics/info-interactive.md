# qCalc Interactivity: Using `interactive` in `__info()`

## Key Flag
Set interactive support in calculator metadata:

- In func__info() return dict: 'interactive': True

If not set (or set False), the calculator runs in manual mode only.

## Effective Enable Conditions
Interactive execution is active only when both conditions are true:

- Calculator metadata enables it: info.interactive == True
- User preference enables it: request.pref.interactive == True

This is expected behavior and should not be bypassed in calculator code.

## Author Expectations
When interactive is enabled:

- Text-like inputs trigger calculate after blur if value changed.
- Standard input/select changes trigger calculate.
- Select2 select/clear/unselect triggers calculate.
- Triggering is debounced to reduce rapid repeated submits.

## Table Inputs
For table-capable calculators (qtable/qtbl):

- Table Update is interactive-compatible.
- Interactive is temporarily suspended during table payload sync.
- Interactive is restored after sync when it was previously enabled.
- One calculate submit is triggered after Update to refresh output.
- Resize/Edit remain structural operations and may require explicit workflow steps.

Design implication:

- Do not assume every table action is equivalent to a normal field change.
- Keep table resize/edit logic safe for full-form structural refresh paths.

## Recommended Metadata Pairing
Use interactive with clear metadata and stable schema:

- Provide clear help_text for fields that can trigger frequent recalculation.
- Keep onsubmit/script hooks idempotent where possible.
- Avoid heavy side effects on each run when interactive is likely.

## Performance Guidance
Interactive can increase submit frequency.

- Prefer lightweight calculations for high-change forms.
- For expensive calculators, keep defaults simple and document manual-calculate option.
- Consider reducing dependency chains in showhide/related/autofill callbacks.

## Validation Checklist
Before release, verify all items:

- info.interactive is explicitly set as intended.
- Interactive toggle appears only when calculator supports interactive.
- Non-table fields auto-calculate as expected.
- Table Update syncs values and refreshes output.
- Resize/Edit do not trigger interactivity.
- Manual Calculate still works in all states.

## Minimal Example
Example metadata fragment:

```python
return {
    'title': 'My Calculator',
    'interactive': True,
    'layout': 'tb',
    'schema': {
        'x': {'help_text': 'Input value'},
    },
}
```

## Common Pitfalls
- Setting interactive=True but forgetting user preference can still disable runtime interactive behavior.
- Treating table Resize/Edit as normal change events.

## Troubleshooting Quick Path
If interactive appears non-functional:

- Confirm info.interactive is True.
- Confirm user pref interactive is True.
- Confirm form renders with interactive button for that calculator.
- Test a simple text field change first, then table Update.
