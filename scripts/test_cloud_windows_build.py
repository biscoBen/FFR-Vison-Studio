import unittest
from unittest.mock import patch

from cloud_windows_build import github_environment, matching_run


class BuildSelectionTests(unittest.TestCase):
    def test_selects_only_new_runs_for_the_requested_branch_and_commit(self):
        runs = [
            {"id": 1, "head_branch": "Sephira's-Update", "head_sha": "wanted", "event": "workflow_dispatch"},
            {"id": 2, "head_branch": "master", "head_sha": "wanted", "event": "workflow_dispatch"},
            {"id": 3, "head_branch": "Sephira's-Update", "head_sha": "old", "event": "workflow_dispatch"},
            {"id": 4, "head_branch": "Sephira's-Update", "head_sha": "wanted", "event": "push"},
            {"id": 5, "head_branch": "Sephira's-Update", "head_sha": "wanted", "event": "workflow_dispatch"},
        ]
        selected = matching_run(runs, branch="Sephira's-Update", commit="wanted", previous_ids={1})
        self.assertEqual(selected["id"], 5)

    def test_no_matching_run_is_not_treated_as_a_success(self):
        self.assertIsNone(matching_run(
            [{"id": 1, "head_branch": "master", "head_sha": "wanted", "event": "workflow_dispatch"}],
            branch="Sephira's-Update", commit="wanted", previous_ids=set(),
        ))

    def test_build_binding_does_not_mutate_the_existing_authentication(self):
        with patch.dict("os.environ", {"GH_TOKEN": "existing-test-binding", "FFR_GITHUB_ACTIONS_TOKEN": "scoped-test-binding"}, clear=True):
            environment = github_environment()
            self.assertEqual(environment["GH_TOKEN"], "scoped-test-binding")
            import os
            self.assertEqual(os.environ["GH_TOKEN"], "existing-test-binding")


if __name__ == "__main__":
    unittest.main()
