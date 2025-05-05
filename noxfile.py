# pylint: skip-file
# type: ignore
# -*- coding: utf-8 -*-
#
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pathlib
import subprocess

import nox


DEFAULT_PYTHON_VERSION = '3.11'

CURRENT_DIRECTORY = pathlib.Path(__file__).parent.absolute()

nox.options.sessions = [
    'format',
]

# Error if a python version is missing
nox.options.error_on_missing_interpreters = True


@nox.session(python=DEFAULT_PYTHON_VERSION)
def format(session):
    """Format Python code using autoflake, pyupgrade, and ruff."""
    # Sort Spelling Allowlist
    spelling_allow_file = '.github/actions/spelling/allow.txt'

    with open(spelling_allow_file, encoding='utf-8') as file:
        unique_words = sorted(set(file))

    with open(spelling_allow_file, 'w', encoding='utf-8') as file:
        file.writelines(unique_words)

    format_all = False

    if format_all:
        lint_paths_py = ['.']
    else:
        target_branch = 'origin/main'

        unstaged_files = subprocess.run(
            [
                'git',
                'diff',
                '--name-only',
                '--diff-filter=ACMRTUXB',
                target_branch,
            ],
            stdout=subprocess.PIPE,
            text=True,
            check=False,
        ).stdout.splitlines()

        staged_files = subprocess.run(
            [
                'git',
                'diff',
                '--cached',
                '--name-only',
                '--diff-filter=ACMRTUXB',
                target_branch,
            ],
            stdout=subprocess.PIPE,
            text=True,
            check=False,
        ).stdout.splitlines()

        committed_files = subprocess.run(
            [
                'git',
                'diff',
                'HEAD',
                target_branch,
                '--name-only',
                '--diff-filter=ACMRTUXB',
            ],
            stdout=subprocess.PIPE,
            text=True,
            check=False,
        ).stdout.splitlines()

        changed_files = sorted(
            {
                file
                for file in (unstaged_files + staged_files + committed_files)
                if os.path.isfile(file)
            }
        )

        lint_paths_py = [f for f in changed_files if f.endswith('.py')]

        if not lint_paths_py:
            session.log('No changed Python files to lint.')
            return

    session.install(
        'types-requests',
        'pyupgrade',
        'autoflake',
        'ruff',
    )

    if lint_paths_py:
        if not format_all:
            session.run(
                'pyupgrade',
                '--exit-zero-even-if-changed',
                '--py311-plus',
                *lint_paths_py,
            )
        session.run(
            'autoflake',
            '-i',
            '-r',
            '--remove-all-unused-imports',
            *lint_paths_py,
        )
        session.run(
            'ruff',
            'check',
            '--fix-only',
            *lint_paths_py,
        )
        session.run(
            'ruff',
            'format',
            *lint_paths_py,
        )
