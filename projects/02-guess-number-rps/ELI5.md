# ELI5 — Guess + RPS

Two games in one folder.

**Guess:** I think of 42, you say 30, I say "higher". You keep trying till "correct".

**RPS:** You show rock, I show scissors — rock wins!

The brain (`game.py`) only decides who wins. The mouth (`cli.py`) talks to you. Because they're separate, we can test the brain without talking.
