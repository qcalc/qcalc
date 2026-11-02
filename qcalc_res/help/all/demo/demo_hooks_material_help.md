# Hooks Demo: Material Mass

## Purpose

This calculator estimates the mass of a piece of metal, wood or plastic from its volume. It is a working demonstration for calculator authors of a form in which the choices of one field depend on another field: when you change the `Material Type`, the list of materials changes with it.

You do not need to know anything about hooks to use it. Select a type, select a material, enter a volume and press `Calculate`.

## Inputs

- `Material Type`: The kind of material: `Metal`, `Wood` or `Plastic`. Changing it rebuilds the form: the list of materials changes and the first material of the new type is selected. The other fields keep what you typed.
- `Material`: The material. The list contains the materials of the selected type, with their density.
- `Volume L`: Volume of the piece in litres. The default is `10`.

### Materials

| Type | Material | Density (kg/m3) |
|---|---|---|
| Metal | Steel | 7850 |
| Metal | Aluminium | 2700 |
| Metal | Copper | 8960 |
| Wood | Oak | 750 |
| Wood | Pine | 500 |
| Wood | Balsa | 160 |
| Plastic | PVC | 1380 |
| Plastic | ABS | 1050 |
| Plastic | Nylon | 1150 |

## Results

- `Density (Kg/M3)`: Density of the selected material.
- `Mass (Kg)`: Mass of the piece.

## Calculation

One cubic metre is 1000 litres.

$$
Mass_{kg} = Density_{kg/m^3} \times \frac{Volume_{L}}{1000}
$$

## Example

- Wood, Pine, `Volume L` 25: `Density (Kg/M3)` is `500` and `Mass (Kg)` is `12.5`.
- Plastic, ABS, `Volume L` 10: `Density (Kg/M3)` is `1050` and `Mass (Kg)` is `10.5`.

## Things to Try

1. Open the calculator. It shows `Metal` and `Steel`. Change `Material Type` to `Wood`: the list now contains `Oak`, `Pine` and `Balsa`, and `Oak` is selected.
2. Type `25` in `Volume L`, then change `Material Type` to `Plastic`. The volume stays `25`, and the material goes back to `PVC`.
3. Select `ABS` and press `Calculate`. Close the calculator and open it again from the catalog: it remembers `Plastic` and `ABS`, and the list of materials matches the remembered type.
4. Open the calculator with a link that names the type, for example `/calc/add/?path=demo_hooks_material/material_type/wood/`. The form opens with the wood materials.

## Important Notes

- This is a demonstration calculator. The densities are typical values. The real mass depends on the grade, the moisture content of wood and any additives in plastic.
- Only the material changes when you change the type. Fields that are not in the list of dependent fields, such as the volume, keep your value.

## For Calculator Authors

The code is in `dem_hooks.py` (`demo_hooks_material`). Three parts work together, and each has a comment in the code:

- The `reload` key of `Material Type` in `__info` rebuilds the form when the type changes and resets the listed fields.
- `__schema` returns the choices of `Material` for the selected type.
- `__input` returns a default material that belongs to the selected type.

The hooks are described in the Calculator hooks guide of the author guide. The first demo, `demo_hooks_quote`, shows `__input`, `__modify`, `__command` and `__help`.
