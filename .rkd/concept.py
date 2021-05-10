from argparse import ArgumentParser
from rkd.api.project import MakefileProjectDefiner
from rkd.standardlib.http import HttpWaitAbstractTask
from rkd.standardlib.shell import ShellCommandAbstractTask


class WaitForApplicationTask(HttpWaitAbstractTask):
    """Wai for application to get up"""

    def get_group_name(self) -> str:
        return ':app'

    def get_name(self) -> str:
        return ':wait'

    def configure(self):
        self.url = 'https://duckduckgo.com'
        self.timeout = 30


class InstallTask(ShellCommandAbstractTask):
    """Install application"""

    def get_name(self) -> str:
        return ':install'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--dev', action='store_true', help='Install dev dependencies?')

    def configure(self):
        self.command = '''
            args=""
            
            if [[ $ARG_DEV ]]; then
                args="${args} --dev"
            fi

            eval "composer install --no-progress ${args}"
        '''


def main(rkd: MakefileProjectDefiner):
    rkd.load_projects(['bahub', 'server'])
    rkd.define_task(WaitForApplicationTask)
    rkd.define_task(InstallTask)
