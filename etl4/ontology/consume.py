from collections.abc import Callable
from abc import abstractmethod
from typing import Tuple, Dict, Iterable

class Consume(Callable):
    """Export data from a set of composites to a single file."""

    def before(self):
        """Optional actions to be performed after the constructor runs but before starting to consume composites."""
        pass

    def after(self):
        """Optional actions to be performed after the composites are all consumed."""

    @abstractmethod
    def consume(self, composite_id: str, composite: Dict):
        pass

    def __call__(self, composites: Iterable[Tuple[str, Dict]]):
        """Generate the export file."""
        self.before()
        for composite_id, composite in composites:
            self.consume(composite_id, composite)
        self.after()
