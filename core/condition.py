import functools

class ConditionWrapper:
    def __init__(self, priority, condition_func):
        self.priority = priority
        self.condition_func = condition_func
        self.event_func = None

    def event(self, func):
        self.event_func = func
        return func

    def __call__(self, *args, **kwargs):
        return self.condition_func(*args, **kwargs)

class ConditionRegistry:
    _conditions = []

    @classmethod
    def register(cls, condition_wrapper):
        cls._conditions.append(condition_wrapper)
        # Sort by priority (Low -> High, so 0 is highest priority)
        cls._conditions.sort(key=lambda x: x.priority)

    @classmethod
    def get_all(cls):
        return cls._conditions

def condition(priority):
    """
    Decorator to register a condition with a priority.
    Usage:
        @condition(priority=0)
        def my_check(...): ...
        
        @my_check.event
        def my_action(...): ...
    
    Args:
        priority (int): The priority of the condition (0 is highest).
    """
    def decorator(func):
        wrapper = ConditionWrapper(priority, func)
        ConditionRegistry.register(wrapper)
        return wrapper
    return decorator
