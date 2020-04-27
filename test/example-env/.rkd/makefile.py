
from rkt_rkd import Component, Task
from rkt_harbor import Harbor

COMPONENTS = [
    Component(Harbor)
]

TASKS = [
    Task('env:test', 'harbor:up', ['--profile=test'])
]
