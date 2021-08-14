
"""
Audit
=====

Allows to keep activity logs for future analysis
"""

import re

from . import env
from .api.syntax import TaskDeclaration
from .context import ApplicationContext


def decide_about_target_log_files(ctx: ApplicationContext, log_to_file: str, declaration: TaskDeclaration,
                                  task_num: int):
    """Decides where to save logs"""

    log_files = []
    session_log: bool = env.audit_session_log_enabled()

    if log_to_file:
        log_files.append(log_to_file)

    if session_log:
        date = ctx.get_creation_date()
        time_with_seconds = date.strftime('%H:%M:%S.%f').replace(':', '_').replace('.', '-')
        template = '.rkd/logs/%DATE-DAY%/%DATE-SECOND%/task-%TASKNUM%-%NORMALIZED_TASKNAME%.log'

        log_files.append(
            template.replace('%DATE-DAY%', date.strftime('%Y-%m-%d'))
                    .replace('%DATE-SECOND%', time_with_seconds)
                    .replace('%TASKNUM%', str(task_num))
                    .replace('%NORMALIZED_TASKNAME%', normalize_task_name_to_filename(declaration))
        )

    return log_files


def normalize_task_name_to_filename(declaration: TaskDeclaration) -> str:
    return re.sub('[^a-zA-Z0-9_]+', '_', declaration.to_full_name()[1:])
