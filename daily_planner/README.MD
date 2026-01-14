1.打包为exe如果出现以下错误
    Traceback (most recent call last):
    File "plyer\utils.py", line 96, in _ensure_obj
    ModuleNotFoundError: No module named 'plyer.platforms'
    Exception in thread Thread-1 (scheduler_engine):
    Traceback (most recent call last):
    File "threading.py", line 1081, in _bootstrap_inner
    File "threading.py", line 1023, in run
    File "daily_planner.py", line 174, in scheduler_engine
    File "plyer\facades\notification.py", line 84, in notify
    File "plyer\facades\notification.py", line 93, in _notify
    NotImplementedError: No usable implementation found!

时需 --collect-submodules plyer 强制包含plyer的所有子模块，
pyinstaller --noconsole --collect-submodules plyer daily_planner.py