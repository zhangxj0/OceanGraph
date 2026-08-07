"""Cost-bounded scheduling helpers for paid QA generation work."""

from __future__ import annotations


def bounded_submission_size(
    remaining_chunks: int,
    max_workers: int,
    remaining_target: int | None,
) -> int:
    """Return the largest safe batch for the current accepted-QA deficit.

    A seed chunk normally yields at most one accepted record.  Restricting the
    in-flight chunk count to the remaining target prevents a run that needs one
    final record from launching an arbitrary minimum batch of paid model calls.
    """

    remaining_chunks = max(0, int(remaining_chunks))
    max_workers = max(1, int(max_workers))
    if remaining_chunks == 0:
        return 0
    if remaining_target is None:
        return min(remaining_chunks, max_workers)
    remaining_target = max(0, int(remaining_target))
    if remaining_target == 0:
        return 0
    return min(remaining_chunks, max_workers, remaining_target)


__all__ = ["bounded_submission_size"]
