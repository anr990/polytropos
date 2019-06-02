from dataclasses import dataclass
import os
import json
from collections.abc import Callable
from abc import abstractmethod
from dataclasses import dataclass
from typing import Tuple, Dict, Iterable
from etl4.ontology.step import Step
from etl4.util.loader import load
from etl4.ontology.task.__paths import TaskPathLocator


# TODO Quimey, unlike the other tasks, consumers may take arguments that are not variables. We may want the ability to
#  do this in general--for example, if a task does a statistical analysis and we want to provide some tuning parameter.
#  I'm not sure if this actually creates a problem or not.
@dataclass
class Consume(Step):
    path_locator: TaskPathLocator
    """Export data from a set of composites to a single file."""
    @classmethod
    def build(cls, path_locator, schema, name, **kwargs):
        consumes = load(path_locator.consumes_dir, cls)
        return consumes[name](path_locator, **kwargs)

    def before(self):
        """Optional actions to be performed after the constructor runs but before starting to consume composites."""
        pass

    def after(self):
        """Optional actions to be performed after the composites are all consumed."""

    @abstractmethod
    def consume(self, composite_id: str, composite: Dict):
        pass

    def __call__(self, origin, target):
        """Generate the export file."""
        self.before()
        for filename in sorted(os.listdir(origin)):
            with open(os.path.join(origin, filename), 'r') as origin_file:
                composite = json.load(origin_file)
                self.consume(filename[:-5], composite)
        self.after()


@dataclass
class ExportToJSON(Consume):
    filename: str

    def __post_init__(self):
        self.fobj = None
        self.first = True

    def before(self):
        self.fobj = open(
            os.path.join(self.path_locator.conf, '../', self.filename), 'w'
        )
        self.fobj.write('{\n')

    def consume(self, composite_id, composite):
        if not self.first:
            self.fobj.write(',\n')
        self.first = False
        self.fobj.write(f'    "{composite_id}": ')
        data = json.dumps(composite, indent=4).split('\n')
        for i, line in enumerate(data):
            if i:
                self.fobj.write('\n')
                self.fobj.write('    ')
            self.fobj.write(line)

    def after(self):
        self.fobj.write('\n}')
        self.fobj.close()


@dataclass
class ExportToCSV(Consume):
    filename: str
    columns: Dict
    invariant: bool

    def consume(self, composite_id, composite):
        pass
