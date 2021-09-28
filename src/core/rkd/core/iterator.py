import abc
from typing import List
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
            aggregated_exceptions += self._handle_task(scheduled, task_num)

            if self.iterate_blocks:
                for block in scheduled.blocks:
                    if block not in blocks_collected:
                        blocks_collected.append(block)

        # iterate over @error and @rescue
        if self.iterate_blocks:
            for block in blocks_collected:
                try:
                    tasks: List[DeclarationScheduledToRun] = block.resolved_error_tasks() + block.resolved_rescue_tasks()
                except:
                    raise Exception("\n".join(block.trace))

                for scheduled in tasks:
                    task_num += 1
                    aggregated_exceptions += self._handle_task(scheduled, task_num)

        if aggregated_exceptions:
            raise AggregatedResolvingFailure(aggregated_exceptions)

    def _handle_task(self, scheduled: DeclarationScheduledToRun, task_num: int):
        """
        Provides error handling for process_task()

        :param scheduled:
        :param task_num:
        :return:
        """

        aggregated_exceptions = []

        try:
            self.process_task(scheduled, task_num)

        except InterruptExecution:
            return aggregated_exceptions

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
