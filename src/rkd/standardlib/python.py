import os
from abc import ABC
from argparse import ArgumentParser
from ..contract import TaskInterface, ExecutionContext
from ..syntax import TaskDeclaration


class BasePythonTask(TaskInterface, ABC):
    def get_group_name(self) -> str:
        return ':py'


class PublishTask(BasePythonTask):
    """ Publishes Python packages to PIP """

    def get_name(self) -> str:
        return ':publish'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--username', help='Username in repository', required=True)
        parser.add_argument('--password', help='Password in repository', required=True)
        parser.add_argument('--skip-existing', help='Do not attempt to release twice', action='store_true')
        parser.add_argument('--test', help='Release to a test test.pypi.org', action='store_true')
        parser.add_argument('--url', help='Repository URL', default='')
        parser.add_argument('--src', help='Source files', default='dist/*')

    def execute(self, context: ExecutionContext) -> bool:
        opts = ''

        if context.args['skip_existing']:
            opts += ' --skip-existing '

        if context.args['url']:
            if context.args['test']:
                raise Exception('Cannot use --url and --test switch at once')

            opts += ' --repository-url=%s' % context.args['url']

        if context.args['test']:
            opts += ' --repository-url https://test.pypi.org/legacy/ '

        self.sh('''
            twine upload \\
                --disable-progress-bar \\
                --verbose \\
                --username=%s \\
                --password=%s \\
                %s %s
        ''' % (
            context.args['username'],
            context.args['password'],
            opts,
            context.args['src']
        ))

        return True


class BuildTask(BasePythonTask):
    """ Builds a Python package in a format to be packaged for publishing """

    def execute(self, context: ExecutionContext) -> bool:
        self.sh('chmod +x setup.py')
        self.sh('./setup.py sdist bdist_wheel %s' % context.args['args'])

        return True

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--args', '-a', help='Optional arguments', required=False, default='')

    def get_name(self) -> str:
        return ':build'


class InstallTask(BasePythonTask):
    """ Install a Python package using setuptools """

    def execute(self, context: ExecutionContext) -> bool:
        self.sh('chmod +x setup.py')
        self.sh('./setup.py install %s' % context.args['args'])

        return True

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--args', '-a', help='Optional arguments', required=False, default='')

    def get_name(self) -> str:
        return ':install'


class CleanTask(BasePythonTask):
    """ Clean up the built Python modules """

    def execute(self, context: ExecutionContext) -> bool:
        context.io.info('Cleaning up the built packages')
        self.sh('rm -rf pbr.egg.info .eggs dist build', verbose=True)

        return not os.path.isdir('pbr.egg.info') and not os.path.isdir('.eggs')

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_name(self) -> str:
        return ':clean'


def imports():
    return [
        TaskDeclaration(CleanTask()),
        TaskDeclaration(PublishTask()),
        TaskDeclaration(BuildTask()),
        TaskDeclaration(InstallTask())
    ]
