"""Compatibility wrapper delegating to nix_adapter.progress."""

from nix_adapter.progress import (
    Progress,
    Task,
    _clean,
    _renderer_main,
    main,
)

__all__ = ["Progress", "Task", "_clean", "_renderer_main", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
