"""Generate report artifacts for the default example run."""

from cohort_describer.pipeline import report_step


if __name__ == "__main__":
    report_step(run_id="r1", out_base="report", formats=("md", "json", "csv"))
    print("Wrote report artifacts")
