"""Temporary: fails on purpose so CI goes red and GitHub emits a check_suite
with conclusion=failure. That delivery is the observable proof that GitHub's
webhook secret matches the deployed one. Removed immediately afterwards.
"""


def test_deliberate_failure_for_webhook_rotation_check():
    assert False, "deliberate - webhook signature rotation check"
