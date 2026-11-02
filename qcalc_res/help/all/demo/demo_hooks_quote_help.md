# Hooks Demo: Paint Quote

## Purpose

This calculator estimates the paint needed to cover a wall and what it costs. The calculation is simple on purpose: the calculator is a working demonstration for calculator authors, and its form and buttons show what the optional hook functions `__info`, `__input`, `__help`, `__modify` and `__command` do.

You do not need to know anything about hooks to use it. Fill the form, press a button, and read the short note next to each field to see what that part of the form does.

## Inputs

- `Prepared By`: Name on the quote. It is filled in when the form opens with your user name, or `guest` when you are not logged in. You can type another name.
- `Quote Date`: The date of the quote. It is filled in with today's date every time the form opens. You can change it.
- `Width`: Width of the wall in feet.
- `Height`: Height of the wall in feet.
- `Coats`: Number of coats of paint, a whole number. The default is `2`.
- `Price per Gal`: Price of one gallon of paint, in any currency. The cost is shown in the same currency.
- `Discount PCT`: Discount on the paint, in percent. The default is `0`.

## Buttons

The buttons under the form do not calculate. They change or check the form, and everything you typed in the other fields stays as it is.

| Button | What it does |
|---|---|
| `Swap width and height` | Exchanges the values of `Width` and `Height`. |
| `Member discount` | Sets `Discount PCT` to `10`. |
| `Clear discount` | Sets `Discount PCT` to `0`. |
| `Check coats` | Shows a message about `Coats`: a warning when it is more than `3`, otherwise a note that it is fine. The value is not changed. |
| `Check inputs` | Checks that `Width` and `Height` are positive and that `Discount PCT` is between `0` and `100`. It shows that the inputs are valid or what to fix, and does not calculate. |
| `What do the hooks see?` | Shows a table of the information a hook function receives: the command, the button data, the values posted by the form and the values the form started with. It is meant for calculator authors. |

Press `Quote` to calculate.

## Results

- `Prepared By`: The name from the form.
- `Quote Date`: The date from the form.
- `Area (Sq Ft)`: Area of the wall.
- `Paint Needed (Gal)`: Gallons of paint needed for all coats.
- `Cost`: Cost of the paint after the discount.

## Calculation

The paint is assumed to cover `350` square feet per gallon.

$$
Area = Width \times Height
$$

$$
Paint = \frac{Area \times Coats}{350}
$$

$$
Cost = Paint \times Price \times \left(1 - \frac{Discount}{100}\right)
$$

## Example

With the default inputs (`Width` 12, `Height` 8, `Coats` 2, `Price per Gal` 40, `Discount PCT` 0) the calculator returns:

- `Area (Sq Ft)`: `96.0`
- `Paint Needed (Gal)`: `0.55`
- `Cost`: `21.94`

After pressing `Member discount` and `Quote` again, the cost is `19.75`.

## Things to Try

1. Open the calculator and note that the date and the name are already filled in. Close it and open it again later: the date is again today's date, because this calculator deliberately does not remember the previous inputs.
2. Type `15` in `Width` and press `Member discount`. The discount changes to `10` and the width stays `15`.
3. Press `Swap width and height`. The two values are exchanged.
4. Type `5` in `Coats` and press `Check coats` to see a warning. The `5` stays in the field.
5. Type `-3` in `Width` and press `Check inputs` to see what has to be fixed.
6. Press `What do the hooks see?`. Notice that the posted values are plain text (`12`), while the values the form started with and the validated values are numbers (`12.0`).

## Important Notes

- This is a demonstration calculator, not painting advice. It estimates one wall with one fixed coverage and ignores windows, doors, waste and surface condition.
- The short text above the form is created by the `__help` function of the calculator and shows the time it was created. This page is the separate help file of the calculator.
- The `Check inputs` and `What do the hooks see?` buttons need a valid form, so enter numbers in the numeric fields first.

## For Calculator Authors

The code is in `dem_hooks.py` (`demo_hooks_quote`). Each hook has a comment that explains what it receives and what it returns. The hooks are described in the Calculator hooks guide of the author guide. The second demo, `demo_hooks_material`, shows `__schema` and the `reload` key.
