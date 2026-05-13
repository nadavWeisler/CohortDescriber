"""Run metrics for the default example run."""

from cohort_describer.pipeline import metrics_step


if __name__ == "__main__":
    rows = metrics_step(run_id="r1")
    print("metric rows written:", rows)
