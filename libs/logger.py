"""Logging utilities: console output plus rotating per-day log files."""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

from datetime import datetime
from pathlib import Path
from typing import TextIO
import inspect
import re
import sys
import traceback

ANSI_COLORS = {
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "green": "\033[32m",
    "magenta": "\033[35m",
    "white": "\033[37m",
    "reset": "\033[0m",
}

LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def _resolve_logger_name(logger_name: str | None, caller_depth: int) -> str:
    if logger_name:
        return logger_name

    frame = inspect.stack()[caller_depth]
    return Path(frame.filename).stem


class _TerminalTee:
    ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

    def __init__(self, original_stream: TextIO, file_path: Path, strip_ansi_for_file: bool = False):
        self.original_stream = original_stream
        self._sinks: list[tuple[Path, bool]] = []
        self.add_sink(file_path, strip_ansi_for_file)

    def add_sink(self, file_path: Path, strip_ansi_for_file: bool = False) -> None:
        sink = (file_path, strip_ansi_for_file)
        if sink not in self._sinks:
            self._sinks.append(sink)

    def write(self, text: str) -> None:
        if not isinstance(text, str):
            text = str(text)

        self.original_stream.write(text)
        self.original_stream.flush()

        for file_path, strip_ansi_for_file in self._sinks:
            file_text = self.ANSI_ESCAPE_RE.sub("", text) if strip_ansi_for_file else text
            with file_path.open("a", encoding="utf-8") as handle:
                handle.write(file_text)

    def flush(self) -> None:
        self.original_stream.flush()

    def isatty(self) -> bool:
        return getattr(self.original_stream, "isatty", lambda: False)()

    @property
    def encoding(self) -> str:
        return getattr(self.original_stream, "encoding", "utf-8")


class ProjectLogger:
    _tee_installed = False
    _original_stdout = sys.stdout
    _original_stderr = sys.stderr
    _stdout_tee: _TerminalTee | None = None
    _stderr_tee: _TerminalTee | None = None

    def __init__(
        self,
        logger_name: str | None = None,
        *,
        capture_terminal: bool = False,
        strip_ansi_for_terminal_log: bool = True,
        log_dir: str | Path | None = None,
        caller_depth: int = 1,
    ) -> None:
        self.logger_name = _resolve_logger_name(logger_name, caller_depth)
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.session_ts = _timestamp()
        self.file_info = self.log_dir / f"{self.logger_name}_{self.session_ts}_info.log"
        self.file_debug = self.log_dir / f"{self.logger_name}_{self.session_ts}_debug.log"
        self.file_error = self.log_dir / f"{self.logger_name}_{self.session_ts}_error.log"
        self.file_terminal = self.log_dir / f"{self.logger_name}_{self.session_ts}_terminal.log"

        if capture_terminal:
            self._install_terminal_capture(self.file_terminal, strip_ansi_for_terminal_log)

    @classmethod
    def _install_terminal_capture(cls, file_path: Path, strip_ansi_for_terminal_log: bool) -> None:
        if cls._tee_installed:
            if cls._stdout_tee is not None:
                cls._stdout_tee.add_sink(file_path, strip_ansi_for_terminal_log)
            if cls._stderr_tee is not None:
                cls._stderr_tee.add_sink(file_path, strip_ansi_for_terminal_log)
            return

        cls._stdout_tee = _TerminalTee(
            original_stream=cls._original_stdout,
            file_path=file_path,
            strip_ansi_for_file=strip_ansi_for_terminal_log,
        )
        cls._stderr_tee = _TerminalTee(
            original_stream=cls._original_stderr,
            file_path=file_path,
            strip_ansi_for_file=strip_ansi_for_terminal_log,
        )
        sys.stdout = cls._stdout_tee
        sys.stderr = cls._stderr_tee
        cls._tee_installed = True

    def _build_prefix(self, level: str) -> str:
        return f"{_timestamp()} [{level}] [{self.logger_name}] "

    def _colorize(self, message: str, color: str | None) -> str:
        if not color:
            return message

        color_key = color.lower()
        if color_key not in ANSI_COLORS:
            return message

        active_stream = sys.stdout
        if not getattr(active_stream, "isatty", lambda: False)():
            return message

        return f"{ANSI_COLORS[color_key]}{message}{ANSI_COLORS['reset']}"

    def _write_line(self, file_path: Path, line: str) -> None:
        """Append one line to a log file, never raising.

        The log directory is recreated if it was removed while the process was
        running, so a missing folder cannot break the code under test.
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass

    def log(self, message: object, logLevel: str = "INFO", color: str | None = None) -> None:
        level = (logLevel or "INFO").upper()
        if level not in LEVELS:
            level = "INFO"

        text = str(message)
        prefix = self._build_prefix(level)
        screen_color = "yellow" if level == "WARNING" and color is None else color
        console_line = prefix + self._colorize(text, screen_color)
        plain_line = prefix + text

        print(console_line, file=sys.stdout, flush=True)

        if level == "DEBUG":
            self._write_line(self.file_debug, plain_line)
        elif level == "ERROR":
            self._write_line(self.file_error, plain_line)
        else:
            self._write_line(self.file_info, plain_line)

    def debug(self, message: object, color: str | None = "cyan") -> None:
        self.log(message, logLevel="DEBUG", color=color)

    def info(self, message: object, color: str | None = None) -> None:
        self.log(message, logLevel="INFO", color=color)

    def warning(self, message: object, color: str | None = "yellow") -> None:
        self.log(message, logLevel="WARNING", color=color)

    def error(self, message: object, color: str | None = "red") -> None:
        self.log(message, logLevel="ERROR", color=color)

    def exception(self, message: str = "Unhandled exception") -> None:
        self.error(f"{message}\n{traceback.format_exc().rstrip()}")

    def section(self, title: str, color: str = "blue", logLevel: str = "INFO") -> None:
        title_line = f"#  {title}  #"
        border = "#" * len(title_line)
        self.log(border, logLevel=logLevel, color=color)
        self.log(title_line, logLevel=logLevel, color=color)
        self.log(border, logLevel=logLevel, color=color)

    def title(self, title: str, color: str = "blue", logLevel: str = "INFO") -> None:
        self.section(title, color=color, logLevel=logLevel)

    def separator(self, char: str = "-", length: int = 60, color: str | None = None, logLevel: str = "INFO") -> None:
        fill_char = char[:1] if char else "-"
        self.log(fill_char * max(length, 1), logLevel=logLevel, color=color)

    def subtitle(self, title: str, color: str = "cyan", logLevel: str = "INFO") -> None:
        self.log(title, logLevel=logLevel, color=color)
        self.separator(char="-", length=len(str(title)), color=color, logLevel=logLevel)

    def log_kv(self, key: str, value: object, color: str | None = None, logLevel: str = "INFO") -> None:
        self.log(f"{key}: {value}", logLevel=logLevel, color=color)

    def success(self, message: object, color: str | None = "green") -> None:
        self.log(message, logLevel="INFO", color=color)

    def blank_line(self) -> None:
        self.log("")

    def __call__(self, message: object, logLevel: str = "INFO", color: str | None = None) -> None:
        self.log(message, logLevel=logLevel, color=color)


def get_logger(
    logger_name: str | None = None,
    *,
    capture_terminal: bool = False,
    strip_ansi_for_terminal_log: bool = True,
    log_dir: str | Path | None = None,
) -> ProjectLogger:
    return ProjectLogger(
        logger_name=logger_name,
        capture_terminal=capture_terminal,
        strip_ansi_for_terminal_log=strip_ansi_for_terminal_log,
        log_dir=log_dir,
    )


class ObjLogger(ProjectLogger):
    def __init__(self, logger_name: str | None = None, log_dir: str | Path | None = None):
        super().__init__(logger_name=logger_name, log_dir=log_dir, caller_depth=2)


class ObjLogger2(ProjectLogger):
    def __init__(
        self,
        logger_name: str | None = None,
        capture_terminal: bool = True,
        strip_ansi_for_terminal_log: bool = False,
        log_dir: str | Path | None = None,
    ):
        super().__init__(
            logger_name=logger_name,
            capture_terminal=capture_terminal,
            strip_ansi_for_terminal_log=strip_ansi_for_terminal_log,
            log_dir=log_dir,
            caller_depth=2,
        )


if __name__ == "__main__":
    logger = ProjectLogger("TestLogger", capture_terminal=True)
    logger.title("LOGGER SELF TEST", color="green")
    logger.subtitle("Standard messages", color="cyan")
    logger.info("Script started", color="green")
    logger.debug("Debugging values...", color="cyan")
    logger.warning("Potential issue detected")
    logger.error("Something went wrong!")
    logger.success("Logger helpers are working")
    logger.separator(char="=", color="magenta")
    logger.log_kv("terminal_capture", True, color="magenta")
