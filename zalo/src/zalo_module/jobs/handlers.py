"""Default job-handler registry.

Each subsystem module provides ``register(handlers: dict)`` and is imported
lazily so a slice not yet landed simply contributes no handlers (its jobs
then fail fast with "no handler registered" instead of crashing the worker).
"""
from __future__ import annotations

import importlib

_HANDLER_MODULES = (
    "zalo_module.jobs.media_jobs",    # MIN-94: media_download + retention sweep
    "zalo_module.jobs.ocr_jobs",      # MIN-95: ocr_default, ocr_request + sweeps
    "zalo_module.jobs.package_jobs",  # MIN-97: package_build + sweeps
)


def build_handlers() -> dict:
    handlers: dict = {}
    for name in _HANDLER_MODULES:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError:
            continue
        mod.register(handlers)
    return handlers


def build_sweepers() -> list:
    """Return registered periodic sweeps ``fn(session, settings)``.

    Sweeps run at the top of each ``run_once`` pass; they are cheap scans that
    enqueue real jobs (e.g. media without OCR -> ``ocr_default``).
    """
    sweepers: list = []
    for name in _HANDLER_MODULES:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError:
            continue
        register = getattr(mod, "register_sweepers", None)
        if register is not None:
            register(sweepers)
    return sweepers
