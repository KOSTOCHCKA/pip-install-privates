import os
import tempfile
from unittest import TestCase

from pip_install_privates.install import collect_requirements


class TestInstall(TestCase):

    def _create_reqs_file(self, reqs):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write('\n'.join(reqs).encode('utf-8'))

        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_considers_all_requirements_in_file(self):
        fname = self._create_reqs_file(['mock==2.0.0', 'nose==1.3.7', 'fso==0.3.1'])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['mock==2.0.0', 'nose==1.3.7', 'fso==0.3.1'])

    def test_removes_comments(self):
        fname = self._create_reqs_file(['mock==2.0.0', '# for testing', 'nose==1.3.7', 'fso==0.3.1'])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['mock==2.0.0', 'nose==1.3.7', 'fso==0.3.1'])

    def test_removes_trailing_comments(self):
        fname = self._create_reqs_file(['mock==2.0.0', 'nose==1.3.7 # for testing', 'fso==0.3.1'])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['mock==2.0.0', 'nose==1.3.7', 'fso==0.3.1'])

    def test_skips_empty_lines(self):
        fname = self._create_reqs_file(['mock==2.0.0', '', 'nose==1.3.7', '', 'fso==0.3.1'])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['mock==2.0.0', 'nose==1.3.7', 'fso==0.3.1'])

    def test_strips_whitespaces(self):
        fname = self._create_reqs_file(['  mock==2.0.0  ', '  ', 'nose==1.3.7  '])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['mock==2.0.0', 'nose==1.3.7'])

    def test_reads_included_files(self):
        basename = self._create_reqs_file(['mock==2.0.0', 'nose==1.3.7'])
        fname = self._create_reqs_file(['-r {}'.format(basename), 'fso==0.3.1'])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['mock==2.0.0', 'nose==1.3.7', 'fso==0.3.1'])

    def test_reads_chain_of_included_files(self):
        file1 = self._create_reqs_file(['mock==2.0.0', 'nose==1.3.7'])
        file2 = self._create_reqs_file(['-r {}'.format(file1), 'Django==1.10'])
        file3 = self._create_reqs_file(['amqp==1.4.7', '-r {}'.format(file2), 'six==1.10.0'])
        file4 = self._create_reqs_file(['-r {}'.format(file3), 'fso==0.3.1'])

        ret = collect_requirements(file4)
        self.assertEqual(ret, ['amqp==1.4.7', 'mock==2.0.0', 'nose==1.3.7',
                               'Django==1.10', 'six==1.10.0', 'fso==0.3.1'])

    def test_honors_vcs_urls(self):
        fname = self._create_reqs_file(['git+https://github.com/ByteInternet/...'])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['git+https://github.com/ByteInternet/...'])

    def test_transforms_vcs_git_url_to_oauth(self):
        fname = self._create_reqs_file(['git+git@github.com:ByteInternet/...'])

        ret = collect_requirements(fname, transform_with_token='my-token')
        self.assertEqual(ret, ['git+https://my-token:x-oauth-basic@github.com/ByteInternet/...'])

    def test_transforms_vcs_git_url_to_oauth_dashe_option(self):
        fname = self._create_reqs_file(['-e git+git@github.com:ByteInternet/...'])

        ret = collect_requirements(fname, transform_with_token='my-token')
        self.assertEqual(ret, ['-e', 'git+https://my-token:x-oauth-basic@github.com/ByteInternet/...'])

    def test_transforms_vcs_ssh_url_to_oauth(self):
        fname = self._create_reqs_file(['git+ssh://git@github.com/ByteInternet/...'])

        ret = collect_requirements(fname, transform_with_token='my-token')
        self.assertEqual(ret, ['git+https://my-token:x-oauth-basic@github.com/ByteInternet/...'])

    def test_transforms_vcs_ssh_url_to_oauth_dashe_option(self):
        fname = self._create_reqs_file(['-e git+ssh://git@github.com/ByteInternet/...'])

        ret = collect_requirements(fname, transform_with_token='my-token')
        self.assertEqual(ret, ['-e', 'git+https://my-token:x-oauth-basic@github.com/ByteInternet/...'])

    def test_transforms_urls_in_included_files(self):
        file1 = self._create_reqs_file(['mock==2.0.0', '-e git+git@github.com:ByteInternet/...', 'nose==1.3.7'])
        fname = self._create_reqs_file(['-r {}'.format(file1), 'fso==0.3.1'])

        ret = collect_requirements(fname, transform_with_token='my-token')
        self.assertEqual(ret, ['mock==2.0.0',
                               '-e', 'git+https://my-token:x-oauth-basic@github.com/ByteInternet/...',
                               'nose==1.3.7', 'fso==0.3.1'])

    def test_transforms_git_plus_git_urls_to_regular_url_if_no_token_provided(self):
        file1 = self._create_reqs_file(['mock==2.0.0', '-e git+git@github.com:ByteInternet/...', 'nose==1.3.7'])
        fname = self._create_reqs_file(['-r {}'.format(file1), 'fso==0.3.1'])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ['mock==2.0.0',
                               '-e', 'git+https://github.com/ByteInternet/...',
                               'nose==1.3.7', 'fso==0.3.1'])

    def test_transforms_git_plus_ssh_urls_to_regular_url_if_no_token_provided(self):
        file1 = self._create_reqs_file(['mock==2.0.0', '-e git+ssh://git@github.com/ByteInternet/...', 'nose==1.3.7'])
        fname = self._create_reqs_file(['-r {}'.format(file1), 'fso==0.3.1'])

        ret = collect_requirements(fname)

        self.assertEqual(ret, ['mock==2.0.0',
                               '-e', 'git+https://github.com/ByteInternet/...',
                               'nose==1.3.7', 'fso==0.3.1'])

    def test_transforms_git_plus_https_urls_to_https_url_with_oauth_token_if_token_provided(self):
        file1 = self._create_reqs_file(['mock==2.0.0', 'git+https://github.com/ByteInternet/...', 'nose==1.3.7'])
        fname = self._create_reqs_file(['-r {}'.format(file1), 'fso==0.3.1'])

        ret = collect_requirements(fname, transform_with_token='my-token')

        self.assertEqual(ret, ['mock==2.0.0',
                               'git+https://my-token:x-oauth-basic@github.com/ByteInternet/...',
                               'nose==1.3.7', 'fso==0.3.1'])

    def test_transforms_editable_git_plus_https_urls_to_editable_https_url_with_oauth_token_if_token_provided(self):
        file1 = self._create_reqs_file(['mock==2.0.0', '-e git+https://github.com/ByteInternet/...', 'nose==1.3.7'])
        fname = self._create_reqs_file(['-r {}'.format(file1), 'fso==0.3.1'])

        ret = collect_requirements(fname, transform_with_token='my-token')

        self.assertEqual(ret, ['mock==2.0.0',
                               '-e', 'git+https://my-token:x-oauth-basic@github.com/ByteInternet/...',
                               'nose==1.3.7', 'fso==0.3.1'])

    def test_does_not_transform_git_plus_https_urls_to_https_url_with_oauth_token_if_no_token_provided(self):
        file1 = self._create_reqs_file(['mock==2.0.0', '-e git+https://github.com/ByteInternet/...', 'nose==1.3.7'])
        fname = self._create_reqs_file(['-r {}'.format(file1), 'fso==0.3.1'])

        ret = collect_requirements(fname)

        self.assertEqual(ret, ['mock==2.0.0',
                               '-e', 'git+https://github.com/ByteInternet/...',
                               'nose==1.3.7', 'fso==0.3.1'])


