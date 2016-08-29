#    Copyright (c) 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import os
import sys

import six

from muranopkgcheck import log
from muranopkgcheck import manager

LOG = log.getLogger(__name__)


def parse_cli_args(args=None):

    usage_string = 'murano-pkg-checker [options] <path to package>'

    parser = argparse.ArgumentParser(
        description='murano-pkg-checker arguments',
        formatter_class=argparse.HelpFormatter,
        usage=usage_string
    )

    parser.add_argument('--select',
                        dest='select',
                        required=False,
                        type=str,
                        help='select errors and warnings (e.g. E001,W002)')

    parser.add_argument('--ignore',
                        dest='ignore',
                        required=False,
                        type=str,
                        help='skip errors and warnings (e.g. E042,W007)')

    parser.add_argument('--verbose', '-v',
                        dest='verbose',
                        default=0,
                        action='count',
                        help='Verbosity level. -v for ERROR. -vv for INFO')

    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='Set logging level to DEBUG')

    parser.add_argument('--discover',
                        dest='discover',
                        action='store_true',
                        help='Run discovery packages')

    parser.add_argument('path',
                        type=str,
                        help='Path to package or catalog')

    return parser.parse_args(args=args)


def setup_logs(args):
    if args.verbose == 0:
        log.setup(level=log.CRITICAL)
    elif args.verbose == 1:
        log.setup(level=log.ERROR)
    else:
        log.setup(level=log.INFO)
    if args.debug:
        log.setup(level=log.DEBUG)


def run(args, pkg_path=None, quiet_load=False):
    m = manager.Manager(pkg_path or args.path, quiet_load=quiet_load)
    m.load_plugins()
    if args.select:
        select = args.select.split(',')
    else:
        select = None
    if args.ignore:
        ignore = args.ignore.split(',')
    else:
        ignore = None
    errors = m.validate(select=select, ignore=ignore)
    fmt = manager.PlainTextFormatter()
    return fmt.format(errors)


def discover(args):
    errors = []
    for dirpath, dirnames, filenames in os.walk(args.path):
        items = dirnames
        for item in items:
            if item.startswith('.'):
                continue
            try:
                path = os.path.join(dirpath, item)
                pkg_errors = run(args, path, quiet_load=True)
                LOG.info("Package {} discovered".format(path))
                if pkg_errors:
                    errors.append("Errors in package {}\n{}\n"
                                  "".format(path, pkg_errors))
            except ValueError:
                pass
    return '\n'.join(errors)


def main():
    args = parse_cli_args()
    setup_logs(args)
    try:
        if args.discover:
            errors = discover(args)
        else:
            errors = run(args)
    except ValueError as e:
        LOG.error(six.text_type(e))
        print(six.text_type(e))
        return 2
    except Exception as e:
        LOG.critical(six.text_type(e), exc_info=sys.exc_info())
        return 3
    if errors:
        print(errors)
        return 1
    else:
        print('No errors found!')

if __name__ == '__main__':
    sys.exit(main())
