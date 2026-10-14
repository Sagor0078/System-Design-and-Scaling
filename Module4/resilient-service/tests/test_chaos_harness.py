"""Metric parsing and verdict logic for the chaos harness.

These run without the stack up; the experiments themselves need containers.
"""

from chaos.run_chaos import EXPERIMENTS, counter_delta, parse_metrics, verdict

SAMPLE = """
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{route="/orders",method="POST",status="200"} 12.0
http_requests_total{route="/orders",method="POST",status="503"} 3.0
circuit_breaker_state{dependency="inventory"} 2.0
degraded_responses_total{route="/orders"} 7.0
some_untyped_metric 1.5
"""


def test_parse_metrics_reads_labelled_series():
    m = parse_metrics(SAMPLE)
    assert m['http_requests_total{method="POST",route="/orders",status="200"}'] == 12.0
    assert m['circuit_breaker_state{dependency="inventory"}'] == 2.0


def test_parse_metrics_reads_unlabelled_series():
    assert parse_metrics(SAMPLE)["some_untyped_metric"] == 1.5


def test_parse_metrics_ignores_comments():
    assert not any(k.startswith("#") for k in parse_metrics(SAMPLE))


def test_parse_metrics_normalises_label_order():
    a = parse_metrics('m{b="2",a="1"} 5.0')
    b = parse_metrics('m{a="1",b="2"} 5.0')
    assert a == b


def test_counter_delta_treats_missing_before_as_zero():
    after = parse_metrics(SAMPLE)
    assert counter_delta({}, after, "degraded_responses_total", {"route": "/orders"}) == 7.0


def test_counter_delta_subtracts_baseline():
    after = parse_metrics(SAMPLE)
    before = {'degraded_responses_total{route="/orders"}': 5.0}
    assert counter_delta(before, after, "degraded_responses_total", {"route": "/orders"}) == 2.0


def test_counter_delta_sums_matching_series_when_labels_partial():
    after = parse_metrics(SAMPLE)
    total = counter_delta(before={}, after=after, name="http_requests_total",
                          labels={"route": "/orders"})
    assert total == 15.0


def test_counter_delta_is_zero_for_unknown_metric():
    assert counter_delta({}, parse_metrics(SAMPLE), "nope_total", {}) == 0.0


def test_verdict_passes_when_all_assertions_hold():
    assert verdict([("breaker opened", True), ("degraded served", True)]) is True


def test_verdict_fails_when_any_assertion_breaks():
    assert verdict([("breaker opened", True), ("no 5xx", False)]) is False


def test_verdict_of_nothing_is_not_a_pass():
    # An experiment that asserted nothing has not proved anything.
    assert verdict([]) is False


def test_experiments_are_named_and_documented():
    names = [e.name for e in EXPERIMENTS]
    assert names == ["total_failure", "latency", "hard_kill", "recovery"]
    assert all(e.description for e in EXPERIMENTS)
