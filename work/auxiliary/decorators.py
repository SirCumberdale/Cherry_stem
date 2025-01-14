from functools import wraps
import time



#TODO: think how to implement log_type in configure logger for only one call
class Logger_decorator:
    """
    A decorator to add logger information to each method used
    ---HAS EXPERIMENTAL FEATURES---
    """
    def __init__(self,logger,log_type="DEBUG"):
        self.logger = logger
        self.log_type = log_type


    def debug_dec(self, func):

        @wraps(func)
        def wrapper_null(*args, **kwargs):
            res = func(*args, **kwargs)
            return res

        @wraps(func)
        def wrapper_time(*args, **kwargs):
            start = time.time()
            res = func(*args, **kwargs)
            end = time.time() - start
            self.logger.debug(f"{func.__qualname__} runtime: {end}")
            return res


        @wraps(func)
        def wrapper_logs(*args, **kwargs):
            self.logger.debug(f" <- {func.__qualname__}")
            res = func(*args, **kwargs)
            self.logger.debug(f" -> {func.__qualname__}")
            return res

        WARPER_TYPES = {"NULL": wrapper_null, "DEBUG": wrapper_logs, "TIME": wrapper_time}
        wrapper = WARPER_TYPES[self.log_type]

        return wrapper
