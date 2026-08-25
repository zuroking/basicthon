# ELI5 — Grades Analyzer

Imagine a table on paper.

- First row is the header: `name,grade` — like column titles.
- Each next row is a student: `Alice,95` means Alice got 95.

What the program does:

- `parse_csv` — reads the paper and makes a pile of cards: `{"name": "Alice", "grade": "95"}`.
- `average` — adds all grades and divides: `90+80=170/2=85`.
- `median` — sorts grades `60,80,90` and picks the middle `80`. If even count `60,80,90,100` → `(80+90)/2=85`.
- `min`/`max` — smallest and biggest card.
- `top_n` — sorts pile biggest first and takes top 3, like a podium.
- `grade_distribution` — sorts cards into 5 buckets: `A` 90+, `B` 80-89, `C` 70-79, `D` 60-69, `F` below 60. Counts each bucket.

Example: `grades.csv` with 4 students → run `python -m grades_analyzer grades.csv` and you get average, median, top 3 and bucket counts printed.

That's it — read CSV, do math, show results.
