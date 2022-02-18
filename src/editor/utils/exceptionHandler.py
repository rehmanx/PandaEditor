import traceback


# TO: DO different exception handlers of log error and return value
def try_execute(func, *args, **kwargs):
    # awful too much garbage collection
    b_should_return_func_val = False
    log_error = True

    if "return_func_val" in kwargs:
        b_should_return_func_val = kwargs.pop("return_func_val")

    if "log_error" in kwargs:
        log_error = kwargs.pop("log_error")

    try:
        val = func(*args, **kwargs)
    except Exception as exc:
        tb_str = traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
        
        print("Exception occurred...!")
        
        if log_error:
            for x in tb_str:
                print(x)
            
        return False

    if b_should_return_func_val:
        return val

    return True
