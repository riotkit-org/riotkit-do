#!/usr/bin/env python3
from textwrap import dedent
import pytest
import os
from rkd.core.api.testing import FunctionalTestingCase

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.e2e
class TestFunctionalPipelines(FunctionalTestingCase):
    """
    Pipelines of tasks - functional tests that spawns full RKD all the time
    """

    def test_pipeline_retries_block_3_times_and_if_rescue_is_defined_then_next_tasks_will_continue_executing(self):
        """
        Given there is a block of tasks
        And middle task exits with 1
        And a @rescue is defined for the block
        And @retry-block is defined to 3

        Then middle task from the block should be retried 3 times
        And the last task in block should execute only ONCE - after middle task would be rescued from failing execution
        And tasks after that whole block should also execute only ONCE

        :return:
        """

        makefile = dedent('''
            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
            from rkd.core.standardlib.core import DummyTask
            from rkd.core.standardlib.shell import ShellCommandTask
        
            PIPELINES = [
                Pipeline(
                    name=':retry-block-example',
                    description='Rescue task example - exit 1 is raised, then a task with exit 0 in rescue is called',
                    to_execute=[
                        Block(rescue=':sh -c "echo \\'rescue is there\\' >> exec.log; exit 0"', retry_block=3, tasks=[
                            Task(':sh', '-c', 'echo "i should be also retried" >> exec.log'),
                            Task(':sh', '-c', 'echo "triggering failure" >> exec.log; exit 1'),
                            Task(':sh', '-c', 'echo "this should be executed only ONCE because of rescue of middle task after 3 retries" >> exec.log'),
                        ]),
                        Task(':sh', '-c', 'echo "I should always execute - single time" >> exec.log'),
                        Task(':sh', '-c', 'echo "And I should always execute too - single time" >> exec.log')
                    ]
                )
            ]
        ''')

        # expect that output will be produced in following way

        # 1) "i should be also retried" -> 1 time executed normally + 3 retries
        # 2) "rescue is there" -> is a rescue for 1), exits with 0 - success, allows next tasks to execute
        # 3) "this should be executed only ONCE..." -> after "i should be also retried" was rescued this task
        #                                              in block can be finally executed
        # 4) all other later tasks are just executed regularly

        expected = dedent('''
            i should be also retried
            triggering failure
            i should be also retried
            triggering failure
            i should be also retried
            triggering failure
            i should be also retried
            triggering failure
            rescue is there
            this should be executed only ONCE because of rescue of middle task after 3 retries
            I should always execute - single time
            And I should always execute too - single time
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.py': makefile}):
            self.run_and_capture_output([':retry-block-example'])

            with open('exec.log') as result:
                self.assertEqual(result.read().strip(), expected.strip())

    def test_pipeline_rescue_without_retry(self):
        """
        Given we have {@rescue #r} #1, #2 {/@} #3 pipeline
        When #1 will fail

        Then those tasks will be executed in order and the pipeline will succeed:
            1. #1
            2. #r
            3. #2
            4. #3

        :return:
        """

        makefile = dedent('''
            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
            from rkd.core.standardlib.core import DummyTask
            from rkd.core.standardlib.shell import ShellCommandTask
    
            PIPELINES = [
                Pipeline(
                    name=':example',
                    to_execute=[
                        Block(rescue=':sh -c "echo \\'#r rescue is there\\' >> exec.log; exit 0"', tasks=[
                            Task(':sh', '-c', 'echo "#1 i should be also retried" >> exec.log; exit 1'),
                            Task(':sh', '-c', 'echo "#2 only once" >> exec.log'),
                        ]),
                        Task(':sh', '-c', 'echo "#3 only once" >> exec.log'),
                    ]
                )
            ]
        ''')

        expected = dedent('''
            #1 i should be also retried
            #r rescue is there
            #2 only once
            #3 only once
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.py': makefile}):
            self.run_and_capture_output([':example'])

            with open('exec.log') as result:
                self.assertEqual(result.read().strip(), expected.strip())

    def test_pipeline_retry_retries_single_task_multiple_times(self):
        """
        Given we have {@rescue #3 @retry 10} #1 {/@} #2
        When #1 fails
        Then #1 will be executed 1 time + 10 times retried
        And after successful execution of #3 rescue task also #2 task will be executed once

        :return:
        """

        makefile = dedent('''
            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
            from rkd.core.standardlib.core import DummyTask
            from rkd.core.standardlib.shell import ShellCommandTask

            PIPELINES = [
                Pipeline(
                    name=':example',
                    to_execute=[
                        Block(rescue=':sh -c "exit 0"', retry=10, tasks=[
                            Task(':sh', '-c', 'echo "#1 i will fail" >> exec.log; exit 1')
                        ]),
                        Task(':sh', '-c', 'echo "#2 finally!" >> exec.log')
                    ]
                )
            ]
        ''')

        expected = dedent('''
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #1 i will fail
            #2 finally!
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.py': makefile}):
            self.run_and_capture_output([':example'])

            with open('exec.log') as result:
                self.assertEqual(result.read().strip(), expected.strip())

    def test_error_does_not_rescue_task_so_the_status_of_whole_execution_will_be_failed(self):
        """
        Given there is a #1 with @error notification that calls #3 in case of failure
        And there is #2 after that block

        Then #1 will be executed
        And #3 task will be executed as an error notification
        But #2 will not execute, due to #1 error without a @rescue defined and working

        :return:
        """

        makefile = dedent('''
            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
            from rkd.core.standardlib.core import DummyTask
            from rkd.core.standardlib.shell import ShellCommandTask

            PIPELINES = [
                Pipeline(
                    name=':example',
                    to_execute=[
                        Block(error=':sh -c "echo \\'#3 error notification\\' >> exec.log; exit 1"', tasks=[
                            Task(':sh', '-c', 'echo "#1 i will fail" >> exec.log; exit 1')
                        ]),
                        Task(':sh', '-c', 'echo "#2 i will not execute" >> exec.log')
                    ]
                )
            ]
        ''')

        expected = dedent('''
            #1 i will fail
            #3 error notification
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.py': makefile}):
            self.run_and_capture_output([':example'])

            with open('exec.log') as result:
                self.assertEqual(result.read().strip(), expected.strip())

    def test_rescue_task_if_fails_then_next_task_would_not_execute_and_whole_execution_status_would_be_failed(self):
        """
        Given there are {@rescue #3} #1, #2 {/@} tasks
        And #1 will fail
        And rescue task #3 will also fail
        Then #2 will not be executed

        :return:
        """

        makefile = dedent('''
            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
            from rkd.core.standardlib.core import DummyTask
            from rkd.core.standardlib.shell import ShellCommandTask

            PIPELINES = [
                Pipeline(
                    name=':example',
                    to_execute=[
                        Block(rescue=':sh -c "echo \\'#3 rescue also fails\\' >> exec.log; exit 1"', tasks=[
                            Task(':sh', '-c', 'echo "#1 i will fail" >> exec.log; exit 1'),
                            Task(':sh', '-c', 'echo "#2 not to be executed" >> exec.log')
                        ])
                    ]
                )
            ]
        ''')

        expected = dedent('''
            #1 i will fail
            #3 rescue also fails
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.py': makefile}):
            self.run_and_capture_output([':example'])

            with open('exec.log') as result:
                self.assertEqual(result.read().strip(), expected.strip())

    def test_default_block_does_not_contain_any_settings(self):
        """
        Given there are #1 and #2 tasks without any block
        And #1 will fail
        Then #2 will not execute

        :return:
        """

        makefile = dedent('''
            from rkd.core.api.syntax import Pipeline, PipelineTask as Task, PipelineBlock as Block, TaskDeclaration
            from rkd.core.standardlib.core import DummyTask
            from rkd.core.standardlib.shell import ShellCommandTask

            PIPELINES = [
                Pipeline(
                    name=':example',
                    to_execute=[
                        Task(':sh', '-c', 'echo "#1 i will fail" >> exec.log; exit 1'),
                        Task(':sh', '-c', 'echo "#2 not to be executed" >> exec.log'),
                    ]
                )
            ]
        ''')

        expected = dedent('''
            #1 i will fail
        ''')

        with self.with_temporary_workspace_containing({'.rkd/makefile.py': makefile}):
            self.run_and_capture_output([':example'])

            with open('exec.log') as result:
                self.assertEqual(result.read().strip(), expected.strip())