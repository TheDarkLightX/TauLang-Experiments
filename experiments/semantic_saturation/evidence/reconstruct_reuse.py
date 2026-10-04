#!/usr/bin/env python3
"""Reconstruct the exact audited reuse archive without overwriting a file."""
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reconstruct(output=None):
    directory = Path(__file__).resolve().parent
    manifest = json.loads((directory / 'reuse-001.parts.json').read_text())
    if manifest.get('schema') != 'tau-lossless-archive-parts/v1':
        raise ValueError('Unsupported archive-parts schema')
    archive = manifest['archive']
    if not isinstance(archive, str) or Path(archive).name != archive or archive in ('', '.', '..'):
        raise ValueError('Unsafe archive name')
    parts = manifest['parts']
    if not isinstance(parts, list) or not parts:
        raise ValueError('Missing ordered parts')
    chunks, names = [], set()
    for index, part in enumerate(parts):
        name = part['path']
        if part['index'] != index or not isinstance(name, str) or Path(name).name != name or name in ('', '.', '..') or name in names:
            raise ValueError('Invalid part order or path')
        names.add(name)
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Part must be a regular nonsymlink file: ' + name)
        data = path.read_bytes()
        if len(data) != part['bytes'] or digest(data) != part['sha256']:
            raise ValueError('Part hash or size mismatch: ' + name)
        chunks.append(data)
    data = b''.join(chunks)
    if len(data) != manifest['archive_bytes'] or digest(data) != manifest['archive_sha256']:
        raise ValueError('Reconstructed archive hash or size mismatch')
    target = Path(output) if output else directory / archive
    if target.is_symlink():
        raise ValueError('Output must not be a symlink')
    if target.exists():
        if not target.is_file() or target.read_bytes() != data:
            raise FileExistsError('Refusing to replace a different existing output')
        status = 'VERIFIED_EXISTING'
    else:
        # Stage in the same directory, then atomically add a destination name.
        # Hard-link creation fails if another file appears; nothing is replaced.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.reuse-part-', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, target)
            status = 'RECONSTRUCTED'
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return {'status': status, 'output': str(target), 'bytes': len(data),
            'sha256': digest(data), 'parts_verified': len(parts)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Optional new output path; default is evidence/reuse-001.tar.gz')
    args = parser.parse_args()
    print(json.dumps(reconstruct(args.output), indent=2, sort_keys=True))
