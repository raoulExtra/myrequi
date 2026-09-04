# Modularity budget

The project keeps files at or below 700 lines where practical.
If a file grows beyond that budget, split it into smaller modules or docs.

## check

- `status` reports files over budget.
- `budget` prints the same report on demand.
- `checkpoint` and `advance` refuse to commit while over-budget files exist.

## future-proofing

- Use the budget as a warning before the file becomes hard to review.
- Prefer smaller support files over one large growing file.
- If a large generated file is necessary, document the exception explicitly.
