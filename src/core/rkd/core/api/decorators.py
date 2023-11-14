from typing import Type


MARKER_SKIP_PARENT_CALL = 'without_parent_marker'
MARKER_CALL_PARENT_FIRST = 'after_parent_marker'
MARKER_CALL_PARENT_LAST = 'before_parent_marker'

ALLOWED_MARKERS = [
    MARKER_SKIP_PARENT_CALL,
    MARKER_CALL_PARENT_FIRST,
    MARKER_CALL_PARENT_LAST
]

MARKERS_MAPPING = {
    'without_parent': MARKER_SKIP_PARENT_CALL,  # default marker (no marker means picking this one)
    'after_parent': MARKER_CALL_PARENT_FIRST,
    'before_parent': MARKER_CALL_PARENT_LAST
}

SUPPORTED_DECORATORS = list(MARKERS_MAPPING.keys())


def without_parent(func):
    """
    Task decorator - no parent call is allowed when inheriting a method

    :param func:
    :return:
    """

    def without_parent_marker():
        return func

    return without_parent_marker


def before_parent(func):
    """
    Task decorator - parent method will be called first, then overridden task (children)

    :param func:
    :return:
    """

    def before_parent_wrapper():
        return func

    return before_parent_wrapper


def after_parent(func):
    """
    Task decorator - parent method will be called last (after children)

    :param func:
    :return:
    """

    def after_parent_wrapper():
        return func

    return after_parent_wrapper


def extends(extend_type: Type):
    """
    Task decorator - points to extends a method

    :param extend_type:
    :return:
    """

    def extends_marker(func):
        func.extends = extend_type
        return func

    return extends_marker
