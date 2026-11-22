"""Windows runner deadline adapter using a kill-on-close Job Object.
Start worker suspended, assign before resume; fail closed on assignment failure.
Requires pywin32, installed and pinned by the consuming workflow.
"""
import time
import subprocess

def run_operation(argv, deadline, *, cwd=None, env=None):
    import win32api, win32con, win32event, win32job, win32process
    remaining=deadline-time.monotonic()
    if remaining<=0: raise TimeoutError("no operation budget")
    job=win32job.CreateJobObject(None,None)
    process=thread=None
    assigned=False
    try:
        limits=win32job.QueryInformationJobObject(job,win32job.JobObjectExtendedLimitInformation)
        limits["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(job,win32job.JobObjectExtendedLimitInformation,limits)
        process,thread,_,_=win32process.CreateProcess(None,subprocess.list2cmdline(argv),None,None,False,win32con.CREATE_SUSPENDED,env,cwd,win32process.STARTUPINFO())
        win32job.AssignProcessToJobObject(job,process)
        assigned=True
        win32process.ResumeThread(thread)
        ms=max(0,min(0xfffffffe,int((deadline-time.monotonic())*1000)))
        if win32event.WaitForSingleObject(process,ms)!=win32con.WAIT_OBJECT_0:
            raise TimeoutError("Windows operation deadline exceeded")
        code=win32process.GetExitCodeProcess(process)
        if code: raise subprocess.CalledProcessError(code,argv)
        return code
    finally:
        if process is not None and not assigned:
            win32api.TerminateProcess(process,1)
        job.Close()
        if thread is not None: thread.Close()
        if process is not None: process.Close()
