#!/usr/bin/env python3
"""Use shared Tau lookup definitions while checking the original VM interface."""
from native_tau_eval import EvalspecTau
from share_lookups import transform


class SharedLookupTau(EvalspecTau):
    def __init__(self, binary, source):
        modified, self.shared_helpers = transform(source)
        self.shared_source = modified
        self.original_request = self.request_line(source)
        self.shared_request = self.request_line(modified)
        self.loaded_shared_source = False
        super().__init__(binary, source=source)

    def _send(self, request, deadline):
        if not self.loaded_shared_source:
            if request != self.original_request:
                raise ValueError('Unexpected initial specification request')
            request = self.shared_request
            self.loaded_shared_source = True
        return super()._send(request, deadline)
