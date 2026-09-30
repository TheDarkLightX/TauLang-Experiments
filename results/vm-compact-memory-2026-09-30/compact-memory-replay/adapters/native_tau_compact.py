#!/usr/bin/env python3
"""Load compact memory equalities and retain the original VM interface."""
from native_tau_shared import SharedLookupTau
from compact_memory import transform


class CompactMemoryTau(SharedLookupTau):
    def __init__(self, binary, source):
        self.compact_source, self.compact_info = transform(source)
        super().__init__(binary, source=source)

    def _send(self, request, deadline):
        if not self.loaded_shared_source:
            self.shared_request = self.request_line(self.compact_source)
        return super()._send(request, deadline)
