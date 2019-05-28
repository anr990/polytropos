from dataclasses import dataclass
from os.path import dirname, basename, isfile, join
import glob
from importlib import import_module
from abc import abstractmethod
from collections.abc import Callable
from typing import Dict

from etl4.ontology.schema import Schema
from etl4.ontology.task.__paths import CHANGES_DIR


@dataclass
class Change(Callable):
    """A transformation to be applied to a single composite. The transformation can create or alter any variable that
    is defined in the schema. As a matter of practice, however, the variables to be altered should be defined in the
    Mutation's parameters."""
    schema: Schema
    lookups: Dict

    @abstractmethod
    def __call__(self, composite: Dict):
        """Perform the change on the supplied composite."""
        pass


def load_changes():
    # stackoverflow magic https://stackoverflow.com/a/1057765/225617
    modules = [
        basename(f)[:-3]
        for f in glob.glob(join(CHANGES_DIR, "*.py"))
        if isfile(f) and not f.endswith('__init__.py')
    ]

    for name in modules:
        import_module('fixtures.conf.changes.' + name)

    return {
        cls.__name__: cls
        for cls in Change.__subclasses__()
    }