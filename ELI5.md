# ELI5: the whole basicthon repository

*ELI5 = "Explain Like I'm 5" — a plain-language explanation with no jargon.
This file is about the repository as a whole; each project folder also has
its own ELI5.*

## What is this thing?

Imagine a **staircase with 20 steps**. Each step is a small computer program
you can read, run and break on purpose — and each step is a little harder
than the one before.

You start at the bottom with a calculator that adds and multiplies. You end
at the top with a real app that has three doors into it: you can type
commands in a terminal, other programs can talk to it over the network, and
everything it remembers survives a restart because it lives in a database
file. Same staircase, twenty evenings or so, and at the top you can look at
most everyday software and think: "I know how the pieces of this fit
together."

## Who built this, and why?

One author (ZuroKing) wanted to prove that a beginner doesn't need video
courses or paid platforms to go from "I know what a variable is" to "I have
built a working web-connected program." So instead of lectures there are 20
finished programs, each small enough to fit in your head, each one commented
and explained like a friendly senior colleague standing behind your chair.

The trick is the **order**. You don't meet databases until you've felt the
pain of losing your to-do list when the program closes. You don't meet web
frameworks until you've built the same features as plain functions first.
Every hard thing arrives exactly when the easier version of it is already
familiar.

## What's inside each step (project)?

Every folder in `projects/` is one self-contained toy:

- A **README** — how to run it and what it teaches,
- An **ELI5** file — the same thing explained even simpler,
- The **actual code** — never more than a few hundred lines,
- **Tests** — little robot checks that prove the code works *without needing
  the internet*.

And here's the neat part: every folder works completely alone. Delete all the
other folders, keep just the calculator — it still runs. It's like 20
standalone LEGO sets instead of one giant box where losing one piece breaks
the castle.

## How would I even read code if I'm not a programmer?

Start with the ELI5 files — they use notebooks, robots and mailmen instead of
functions and servers. Then open any README: the "Usage" sections show what
to type, and you can copy-paste those commands without understanding them yet.
Only then peek into `src/`, where the actual Python lives — by project 05 or
so, if you go in order, you'll be surprised how much of it just reads like
English sentences.

You will need Python installed on your computer (it's free). Every project's
README starts with the exact two commands to type. That's the whole barrier
to entry.

## Is anything here dangerous?

No — but some projects *look* serious. One of them manages passwords, another
handles login screens. They work correctly for learning purposes, but they're
deliberately simplified — like a driving simulator rather than a real car.
They say so loudly, in big letters, in their READMEs and in the SECURITY
file. The rule is simple: learn from these programs, don't trust them with
anything real.

## Why does everything repeat? (tests, notes, two languages)

Because repetition is how beginners recognize patterns:

- Every project has tests so you can *see* that the code works before reading
  a single line — and so you learn that checking your own work is normal, not
  optional.
- Every project has a note from the author explaining the one non-obvious
  idea hidden inside — the reason that project exists at all.
- Everything comes in English and Russian, because the audience asked for
  both, and translating forces explanations to stay simple.

## TL;DR

- A staircase of 20 small, working Python programs, easy → harder.
- Each one runs alone; no missing pieces, no setup hell.
- Read ELI5 first, README second, code third.
- Nothing here needs the internet, accounts, or money.
- The password-manager and login projects are toys — great teachers,
  terrible bodyguards.

Ready to climb? Start at [projects/01-cli-calculator/](projects/01-cli-calculator/).
