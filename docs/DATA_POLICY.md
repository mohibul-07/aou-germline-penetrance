# Data policy

This repository is **code and documentation only**.

Never commit:
- Participant-level data: anything with `person_id`/`research_id`, cohort tables, carrier lists,
  phenotype tables, genotypes, notebook outputs.
- Controlled-tier derivatives: VAT extracts, variant lists with All of Us allele counts, ancestry files,
  ACMG/annotation outputs over All of Us variants.
- Aggregate counts between 1 and 20 (All of Us Data and Statistics Dissemination Policy). Suppress or
  bin small cells in any exported table or figure.
- Licensed data: OMIM `genemap2.txt`.
- Large public references (FASTA, GFF3, SA databases): scripts rebuild them.

Before committing a notebook: **Edit -> Clear All Outputs**. The pre-commit hook enforces this.

Install the hook: `ln -s ../../hooks/pre-commit .git/hooks/pre-commit`

Third-party material: the OMOP cancer concept mapping is Rita Lu's (Huang Lab) — ask before publishing.


## Code-export clarification
Column names such as person_id and research_id are required in code; actual identifiers and embedded participant rows are prohibited. Synthetic tests use invented identifiers/keys and artificial counts only, not observed outputs. Numeric thresholds, concept IDs, coordinates in the user-provided public panel config, dates and layout sizes are not participant cell counts. The panel BED was already present; its coordinate convention still needs confirmation.

The inclusive small-cell interval is 1–20. Zero can be shown only when otherwise appropriate; positive counts must exceed 20, and complementary/marginal disclosure must also be reviewed. No aggregate has been certified for release by this code-only export. No new dataset files or notebook outputs are included. Paths alone do not authorize access or sharing.
