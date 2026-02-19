from pathlib import Path

from eval.runner import run_evals


def test_eval_runner_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "results.json"
    report = run_evals(output_path=output)

    assert output.exists()
    assert report["summary"]["total"] == 3
    assert len(report["results"]) == 3
