"""Run checks for the default example run."""

from cohort_describer.pipeline import checks_step


if __name__ == "__main__":
    n = checks_step(run_id="r1")
    print("checks written:", n)
