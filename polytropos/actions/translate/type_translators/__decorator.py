from typing import Type, Callable

from polytropos.actions.translate.__type_translator_register import register_type_translator_class


def type_translator(variable_type: Type) -> Callable[[Type], Type]:
    def wrap(cls: Type) -> Type:
        register_type_translator_class(variable_type, cls)
        return cls

    return wrap
