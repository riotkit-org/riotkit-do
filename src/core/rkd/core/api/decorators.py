from typing import Type


def no_parent_call(func):
    """
    Task decorator - no parent call is allowed when inheriting a method

    :param func:
    :return:
    """

    def no_parent_call_wrapper():
        func.wrapper = 'no_parent_call_wrapper'
        return func

    return no_parent_call_wrapper


def call_parent_first(func):
    """
    Task decorator - parent method will be called first, then overridden task (children)

    :param func:
    :return:
    """

    def call_parent_first_wrapper():
        func.wrapper = 'call_parent_first_wrapper'
        return func

    return call_parent_first_wrapper


def extends(extend_type: Type):
    """
    Task decorator - points to extends a method

    :param extend_type:
    :return:
    """

    def extends_wrapper(func):
        func.wrapper = 'extends_wrapper'
        func.extends = extend_type
        return func

    return extends_wrapper
