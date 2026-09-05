# Can the Stars Beat the Stats?

Bachelor's thesis project investigating whether same-day zodiac-based signals contain predictive information about individual player performance in the English Premier League.

## Thesis scope

The project will compare:

1. Conventional football-statistics predictions
2. Same-day zodiac-based predictions
3. A combined football + zodiac model

The main experiment will use performances from earlier Premier League matches on a given day to generate zodiac signals for players appearing in later matches.

## Current status

This repository is being refactored from an earlier exploratory astrology-football project.

The existing 2023 and 2024 datasets are considered legacy data because they:
- do not contain all Premier League teams,
- are not fully up to date,
- do not contain reliable kickoff timestamps for chronological prediction,
- and were originally created for exploratory analysis rather than thesis evaluation.

A new complete dataset will be generated for the thesis.

## Planned structure

- `src/data/` – data collection and processing
- `src/features/` – football and zodiac feature generation
- `src/models/` – prediction models
- `src/evaluation/` – backtesting and statistical tests
- `src/utils/` – shared utilities
- `data/raw/` – raw API data
- `data/processed/` – cleaned thesis datasets
- `data/reference/` – player birth dates and other reference data
- `legacy/` – archived exploratory scripts