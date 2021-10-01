import abc
from typing import List, Tuple
from .api.syntax import DeclarationScheduledToRun
from .argparsing.model import ArgumentBlock
from .exception import AggregatedResolvingFailure, InterruptExecution
from .resolver_result import ResolvedTaskBag


class TaskIterator(abc.ABC):
    def iterate(self, tasks: ResolvedTaskBag):
        aggregated_exceptions = []
        task_num = 0
        blocks_collected: List[ArgumentBlock] = []

        for scheduled in tasks.scheduled_declarations_to_run:
            task_num += 1

            try:
                aggregated_exceptions += self._handle_task(scheduled, task_num, aggregated_exceptions)

            except InterruptExecution:
                raise AggregatedResolvingFailure(aggregated_exceptions)

            if self.iterate_blocks:
                for block in scheduled.blocks:
                    if block not in blocks_collected:
                        blocks_collected.append(block)

        # OPTIONALLY iterate over @error and @rescue
        if self.iterate_blocks:
            for block in blocks_collected:
                tasks: List[DeclarationScheduledToRun] = block.resolved_error_tasks() + block.resolved_rescue_tasks()

                for scheduled in tasks:
                    task_num += 1
                    aggregated_exceptions += self._handle_task(scheduled, task_num, aggregated_exceptions)

        if aggregated_exceptions:
            raise AggregatedResolvingFailure(aggregated_exceptions)

    def _handle_task(self, scheduled: DeclarationScheduledToRun, task_num: int, aggregated_exceptions: list):
        """
        Provides error handling for process_task()

        :param scheduled:
        :param task_num:
        :return:
        """

        try:
            self.process_task(scheduled, task_num)

        except InterruptExecution:
            raise

        except Exception as err:
            if self.fail_fast is False:
                aggregated_exceptions.append(err)
            else:
                raise err

        return aggregated_exceptions

    @property
    def fail_fast(self) -> bool:
        return False

    @property
    def iterate_blocks(self) -> bool:
        return False

    @abc.abstractmethod
    def process_task(self, scheduled: DeclarationScheduledToRun, task_num: int):
        pass
