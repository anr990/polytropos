import logging
import os
from shutil import rmtree
import yaml
from tempfile import TemporaryDirectory
from etl4.ontology.metamorphosis import Metamorphosis
from etl4.ontology.scan import Scan
from etl4.ontology.filter import Filter
from etl4.ontology.aggregation import Aggregation

from etl4.ontology.step import Step
from etl4.ontology.schema import Schema
from etl4.ontology.translate_step import TranslateStep
from etl4.ontology.task.__paths import TaskPathLocator


# Step class name deserialization
STEP_TYPES = {
    cls.__name__: cls
    for cls in Step.__subclasses__()
}


class Task:
    def __init__(
        self, path_locator,
        origin_data, origin_schema,
        target_data=None, target_schema=None
    ):
        logging.info("Constructing Task object based on configuration file..")
        self.path_locator = path_locator
        self.origin_data = origin_data
        self.origin_schema = origin_schema
        self.target_data = target_data
        self.target_schema = target_schema
        self.steps = []

    @classmethod
    def build(cls, conf_dir, data_dir, name):
        """Build task from yaml, read all input data and create corresponding
        objects"""
        path_locator = TaskPathLocator(conf=conf_dir, data=data_dir)
        logging.info("Loading task configuration from disk.")
        task_filename: str = os.path.join(path_locator.tasks_dir, name + '.yaml')
        logging.info("Task filename: %s" % task_filename)
        with open(
                task_filename, 'r'
        ) as f:
            spec = yaml.safe_load(f)
        resulting_in = spec.get('resulting_in', {})
        task = cls(
            path_locator=path_locator,
            origin_data=spec['starting_with']['data'],
            origin_schema=Schema.load(
                path_locator, spec['starting_with']['schema']
            ),
            target_data=resulting_in.get('data'),
            target_schema=Schema.load(
                path_locator, resulting_in.get('schema')
            )
        )
        task.load_steps(spec['steps'])
        # If the last step is a Consume step we don't need target data
        assert task.target_data is not None or isinstance(task.steps[-1], Consume)
        return task

    def load_steps(self, step_descriptions):
        """Load steps of the current task"""
        logging.info("Loading task steps.")
        current_schema = self.origin_schema
        for step in step_descriptions:
            # expect only one key/value pair
            assert len(step) == 1, (
                'Step description can have only one key, value pair'
            )
            for cls_name, kwargs in step.items():
                logging.info(" - Loading %s step." % cls_name)
                step_instance = STEP_TYPES[cls_name].build(
                    path_locator=self.path_locator, schema=current_schema, **kwargs
                )
                self.steps.append(step_instance)
                # Aggregation changes schema
                if cls_name in ('Aggregation', 'TranslateStep'):
                    current_schema = step_instance.target_schema

    def run(self):
        """Run the task: run steps one by one handling intermediate outputs in
        temporary folders"""
        origin_path = os.path.join(self.path_locator.entities_dir, self.origin_data)
        if self.target_data is not None:
            actual_path = os.path.join(
                self.path_locator.entities_dir, self.target_data
            )
            try:
                rmtree(actual_path)
            except FileNotFoundError:
                pass
            os.mkdir(actual_path)
        # There are always two paths in play, current and next, each step
        # will read from current and write to next, after the step is done we
        # can delete the current_path folder because it's not used anymore
        current_path = origin_path
        current_path_obj = None
        next_path = None
        for step in self.steps:
            next_path = TemporaryDirectory(dir=self.path_locator.data_dir)
            step(current_path, next_path.name)
            if current_path_obj:
                current_path_obj.cleanup()
            current_path = next_path.name
            current_path_obj = next_path
        if self.target_data is not None:
            # Move the last temporary folder to destination
            os.rename(next_path.name, actual_path)
            # Hack to avoid leaving unfinished objects
            os.mkdir(next_path.name)
        next_path.cleanup()
