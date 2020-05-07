
import yaml
from typing import List
from .exception import YamlParsingException
from .inputoutput import SystemIO
from .context import Context
from .syntax import TaskDeclaration


class YamlContextFactory:
    io: SystemIO

    def __init__(self, io: SystemIO):
        self.io = io

    def parse(self, content: str):
        parsed = yaml.parse(content)

        if "imports" in parsed:
            imports = self._parse_imports(parsed['imports'])

        if "tasks" not in parsed:
            raise YamlParsingException('"tasks" section not found in YAML file')

    def _parse_imports(self, classes: List[str]) -> List[TaskDeclaration]:
        parsed = []

        for importstr in classes:
            parts = importstr.split('.')
            classname = parts[-1]
            import_path = parts[:-1]


