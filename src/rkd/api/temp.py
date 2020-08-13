import os
from typing import Tuple
from typing import List
from uuid import uuid4
from os import unlink as delete_file
from os import chmod
from os import mkdir
from os.path import realpath


class TempManager(object):
    """
    Manages temporary files inside .rkd directory
    Using this class you make sure your code is more safe to use on Continuous Integration systems (CI)

    Usage:
        path = self.temp.assign_temporary_file(mode=0o755)

    """

    assigned: List[str]
    chdir: str

    def __init__(self, chdir: str = './.rkd/'):
        self.assigned = []
        self.chdir = chdir

    def create_tmp_file_path(self) -> Tuple[str, str]:
        tmp_vault_filename = '.tmp-' + str(uuid4())
        tmp_vault_path = self.chdir + tmp_vault_filename

        self.assigned.append(tmp_vault_path)

        return tmp_vault_path, tmp_vault_filename

    def assign_temporary_file(self, mode: int = 0o755) -> str:
        """Assign a path for writing temporary files in RKD workspace

        Note: The RKD is executing the finally_clean_up() at the end of each task

        Usage:
            try:
                path = RKDTemp.assign_temporary_file_path()
                # (...) some action there

            finally:
                RKDTemp.finally_clean_up()

        """

        if not os.path.isdir(self.chdir):
            mkdir(self.chdir)

        path = self.create_tmp_file_path()[0]

        with open(path, 'w') as f:
            f.write('')

            chmod(path=path, mode=mode)

        return realpath(path)

    def finally_clean_up(self):
        """Used to clean up all temporary files at the end of the code execution

        TaskExecutor is running this method after each finished task
        """

        for path in self.assigned:
            try:
                delete_file(path)
            except Exception:
                pass

        self.assigned = []
