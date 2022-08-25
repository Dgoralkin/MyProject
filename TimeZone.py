from datetime import datetime
from pytz import timezone




def time_UTC_to_IL():
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    now_IL = datetime.now(timezone('Israel'))
    now_IL_str = now_IL.strftime('%Y-%m-%d %H:%M:%S.%f')
    now_IL_dt = datetime.strptime(now_IL_str, fmt)

    print("now_utc", type(datetime.now()), datetime.now())
    print("now_il", type(now_IL_dt), now_IL_dt)
    
    return now_IL_dt

timeIL = time_UTC_to_IL()
print("time", type(timeIL), timeIL)