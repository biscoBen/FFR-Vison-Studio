"""Run the usual unittest discovery; expose failure tracebacks in CI annotations.

Raw Actions log storage is not always reachable from the cloud workspace. These
annotations retain the exact test failure without skipping any required checks.
"""
import argparse
import os
import sys
import unittest


def escape(value):
    return value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


class AnnotatedResult(unittest.TextTestResult):
    def annotate(self, test, traceback):
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            print('::error title=Python regression::' + escape(test.id() + '\n' + traceback[-12000:]), flush=True)

    def addError(self, test, error):
        super().addError(test, error)
        self.annotate(test, self.errors[-1][1])

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.annotate(test, self.failures[-1][1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-s', '--start-directory', default='scripts')
    parser.add_argument('-p', '--pattern', default='test_*.py')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print('::notice title=Python runtime::' + escape(sys.version + '\n' + sys.executable), flush=True)
    suite = unittest.defaultTestLoader.discover(args.start_directory, pattern=args.pattern)
    result = unittest.TextTestRunner(verbosity=2 if args.verbose else 1, resultclass=AnnotatedResult).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
