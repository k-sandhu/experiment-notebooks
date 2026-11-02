"""Windows job accounting. Children enter the job before their first instruction."""

import ctypes as ct
from ctypes import wintypes as wt
import os
import struct
import subprocess
import time
from pathlib import Path

import psutil

from bench import config as C

SIZE_T = ct.c_size_t
U64 = ct.c_ulonglong
I64 = ct.c_longlong
HANDLE = wt.HANDLE


class BasicLimits(ct.Structure):
    _fields_ = [("PerProcessUserTimeLimit", I64), ("PerJobUserTimeLimit", I64),
                ("LimitFlags", wt.DWORD), ("MinimumWorkingSetSize", SIZE_T),
                ("MaximumWorkingSetSize", SIZE_T), ("ActiveProcessLimit", wt.DWORD),
                ("Affinity", SIZE_T), ("PriorityClass", wt.DWORD), ("SchedulingClass", wt.DWORD)]


class IOCounters(ct.Structure):
    _fields_ = [(name, U64) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                       "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class ExtendedLimits(ct.Structure):
    _fields_ = [("BasicLimitInformation", BasicLimits), ("IoInfo", IOCounters),
                ("ProcessMemoryLimit", SIZE_T), ("JobMemoryLimit", SIZE_T),
                ("PeakProcessMemoryUsed", SIZE_T), ("PeakJobMemoryUsed", SIZE_T)]


class Accounting(ct.Structure):
    _fields_ = [(name, I64) for name in ("TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime", "ThisPeriodTotalKernelTime")] + [
        (name, wt.DWORD) for name in ("TotalPageFaultCount", "TotalProcesses", "ActiveProcesses", "TotalTerminatedProcesses")]


class MemoryCounters(ct.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD)] + [(name, SIZE_T) for name in (
        "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
        "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]


def api():
    if os.name != "nt":
        raise OSError("This benchmark requires Windows job objects")
    kernel = ct.WinDLL("kernel32", use_last_error=True)
    declarations = {
        "CreateJobObjectW": ([ct.c_void_p, wt.LPCWSTR], HANDLE),
        "SetInformationJobObject": ([HANDLE, ct.c_int, ct.c_void_p, wt.DWORD], wt.BOOL),
        "QueryInformationJobObject": ([HANDLE, ct.c_int, ct.c_void_p, wt.DWORD, ct.c_void_p], wt.BOOL),
        "AssignProcessToJobObject": ([HANDLE, HANDLE], wt.BOOL),
        "TerminateJobObject": ([HANDLE, wt.UINT], wt.BOOL),
        "CloseHandle": ([HANDLE], wt.BOOL),
        "GetSystemCpuSetInformation": ([ct.c_void_p, wt.ULONG, ct.POINTER(wt.ULONG), HANDLE, wt.ULONG], wt.BOOL),
    }
    for name, (args, result) in declarations.items():
        function = getattr(kernel, name)
        function.argtypes, function.restype = args, result
    return kernel


def checked(success):
    if not success:
        raise ct.WinError(ct.get_last_error())


def cpu_sets():
    import psutil
    fallback = dict(p_cores=list(range(psutil.cpu_count())), e_cores=[], cpu_sets=[],
                    affinity_detection="fallback: all processors")
    try:
        kernel = api()
        length = wt.ULONG()
        kernel.GetSystemCpuSetInformation(None, 0, ct.byref(length), None, 0)
        if length.value == 0:
            raise ct.WinError(ct.get_last_error())
        buffer = ct.create_string_buffer(length.value)
        checked(kernel.GetSystemCpuSetInformation(buffer, length.value, ct.byref(length), None, 0))
        raw, offset, rows = buffer.raw, 0, []
        while offset < length.value:
            size, kind = struct.unpack_from("<II", raw, offset)
            if size < 8 or offset + size > length.value:
                raise ValueError("invalid CPU-set record size")
            if kind == 0 and size >= 32:
                rows.append(dict(id=struct.unpack_from("<I", raw, offset + 8)[0],
                                 group=struct.unpack_from("<H", raw, offset + 12)[0],
                                 logical=raw[offset + 14], core=raw[offset + 15], efficiency=raw[offset + 18]))
            offset += size
        if not rows or any(row["group"] != 0 for row in rows):
            raise ValueError("multiple processor groups or no CPU-set records; job affinity mask unavailable")
        highest = max(row["efficiency"] for row in rows)
        return dict(p_cores=[r["logical"] for r in rows if r["efficiency"] == highest],
                    e_cores=[r["logical"] for r in rows if r["efficiency"] < highest], cpu_sets=rows,
                    affinity_detection="GetSystemCpuSetInformation: highest EfficiencyClass")
    except (OSError, ValueError) as exc:
        fallback["affinity_detection"] += f" ({exc})"
        return fallback


class Job:
    def __init__(self, processors=None):
        self.kernel = api()
        self.handle = self.kernel.CreateJobObjectW(None, None)
        checked(self.handle)
        self.affinity = "all" if processors is None else ",".join(map(str, processors))
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
        if processors is not None:
            limits.BasicLimitInformation.LimitFlags |= 0x10  # AFFINITY
            limits.BasicLimitInformation.Affinity = sum(1 << i for i in processors)
        try:
            checked(self.kernel.SetInformationJobObject(self.handle, 9, ct.byref(limits), ct.sizeof(limits)))
        except BaseException:
            self.close()
            raise

    def query(self, kind, structure):
        result = structure()
        checked(self.kernel.QueryInformationJobObject(self.handle, kind, ct.byref(result), ct.sizeof(result), None))
        return result

    def launch(self, command, **kwargs):
        process = subprocess.Popen(command, creationflags=0x00000004 | 0x08000000, **kwargs)
        try:
            checked(self.kernel.AssignProcessToJobObject(self.handle, HANDLE(int(process._handle))))
            resume = ct.WinDLL("ntdll").NtResumeProcess
            resume.argtypes, resume.restype = [HANDLE], ct.c_long
            status = resume(HANDLE(int(process._handle)))
            if status < 0:
                raise OSError(f"NtResumeProcess returned NTSTATUS {status:#x}")
        except BaseException:
            process.kill()
            process.wait()
            raise
        return process

    def kill(self):
        checked(self.kernel.TerminateJobObject(self.handle, 124))

    def process_ids(self):
        capacity = 128
        while True:
            buffer = ct.create_string_buffer(8 + ct.sizeof(SIZE_T) * capacity)
            if self.kernel.QueryInformationJobObject(self.handle, 3, buffer, len(buffer), None):
                count = struct.unpack_from("<II", buffer.raw)[1]
                return list((SIZE_T * count).from_buffer_copy(buffer.raw[8:8 + count * ct.sizeof(SIZE_T)]))
            if ct.get_last_error() != 234:  # ERROR_MORE_DATA
                raise ct.WinError(ct.get_last_error())
            capacity *= 2

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def run(command, cwd, stdout_path, stderr_path, timeout, *, processors=None, env=None):
    """Wait for the complete job, preserving handles until all counters are read."""
    stdout_path, stderr_path = Path(stdout_path), Path(stderr_path)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    Path(cwd).mkdir(parents=True, exist_ok=True)
    with Job(processors) as job, stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        system_before = psutil.cpu_times()
        start = time.perf_counter()
        process = job.launch(command, cwd=cwd, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                             env=C.environment() if env is None else env)
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            job.kill()
            process.wait()
        wall = time.perf_counter() - start
        system_after = psutil.cpu_times()
        # Rustup can leave an orphan console host alive after cargo exits. Time the
        # root's lifetime, then stop residual descendants before taking counters.
        active_at_exit = job.query(1, Accounting).ActiveProcesses
        if active_at_exit:
            job.kill()
            deadline = time.perf_counter() + C.JOB_CLEANUP_TIMEOUT
            while job.query(1, Accounting).ActiveProcesses:
                if time.perf_counter() > deadline:
                    raise OSError("Job still has active processes after TerminateJobObject")
                time.sleep(C.JOB_POLL_SECONDS)
        accounting, limits = job.query(1, Accounting), job.query(9, ExtendedLimits)
        memory = MemoryCounters()
        memory.cb = ct.sizeof(memory)
        get_memory = ct.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
        get_memory.argtypes, get_memory.restype = [HANDLE, ct.c_void_p, wt.DWORD], wt.BOOL
        checked(get_memory(HANDLE(int(process._handle)), ct.byref(memory), ct.sizeof(memory)))
        user, kernel = accounting.TotalUserTime / 1e7, accounting.TotalKernelTime / 1e7
        # Busy CPU seconds on the whole machine minus the job's own: other load during the run, in cores.
        deltas = {field: getattr(system_after, field) - getattr(system_before, field) for field in system_after._fields}
        system_busy = sum(deltas.values()) - deltas["idle"]
        result = dict(wall_seconds=wall, user_seconds=user, kernel_seconds=kernel, cpu_seconds=user + kernel,
                      cpu_wall_ratio=(user + kernel) / wall, peak_job_commit=limits.PeakJobMemoryUsed,
                      peak_process_commit=limits.PeakProcessMemoryUsed, peak_working_set=memory.PeakWorkingSetSize,
                      processes=accounting.TotalProcesses, exit_code=process.returncode, timed_out=timed_out,
                      affinity=job.affinity, active_at_exit=active_at_exit,
                      other_busy_cores=max(0.0, system_busy - user - kernel) / wall)
        # Popen retains its process handle after wait; release it after memory inspection.
        process._handle.Close()
        return result
