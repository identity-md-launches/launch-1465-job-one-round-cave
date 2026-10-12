#!/usr/bin/env python3
"""Carry validated ERC-20 windows and recomputable receipts in offline handoffs."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile


HERE = Path(__file__).resolve().parent
MAX_BYTES = 99000
CAPTURE = 'evidence/transfer-window.json'
RECEIPT = 'evidence/window-receipt.json'
NOTE = ('Integrity and local evidence validation only; no completeness, finality, '
        'provider honesty, balance, sender identity or execution safety established.')


def load(name, folder, filename):
    path = HERE / 'vendor' / folder / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


handoff = load('window_handoff_producer', 'handoff', 'handoff.py')
inspector = load('window_handoff_inspector', 'handoff-inspect', 'inspect_handoff.py')
portability = load('window_handoff_portability', 'handoff-portability', 'portability.py')
receipts = load('window_handoff_receipts', 'transfer-window-receipt', 'receipt.py')
crosscheck = receipts.crosscheck
window = crosscheck.window
LIMITS = inspector.Limits(archive_bytes=MAX_BYTES, payload_bytes=MAX_BYTES,
                         manifest_bytes=4096, metadata_bytes=4096, files=2)


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('non-finite JSON value')


def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('JSON exceeds 99,000 bytes')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                      parse_constant=invalid_constant)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii') + b'\n'


def checked_receipt(capture):
    # Rebuild events and all inherited anchors/counts from raw logs first.
    result = receipts.receipt(capture)
    checked = crosscheck.checked(capture)
    if canonical(capture['transfers']) != canonical(checked['transfers']):
        raise ValueError('transfer summary differs in JSON types or values')
    if 'address_window_summary' in capture:
        if capture['schema_version'] != 3:
            raise ValueError('address summary requires schema 3')
        saved = capture['address_window_summary']
        if not isinstance(saved, dict):
            raise ValueError('address summary must be an object')
        try:
            selected = window.address(saved.get('address'))
        except argparse.ArgumentTypeError as error:
            raise ValueError('invalid summary address') from error
        expected = window.address_summary(capture['transfers'], selected, capture['decimals'])
        # Canonical bytes distinguish boolean 1 from integer 1, unlike dict ==.
        if canonical(saved) != canonical(expected):
            raise ValueError('address summary disagrees with validated transfers')
    return result


def build(raw):
    capture = parse(raw)
    receipt = checked_receipt(capture)
    data = handoff.build({CAPTURE: raw, RECEIPT: canonical(receipt)})
    if len(data) > MAX_BYTES:
        raise ValueError('handoff exceeds 99,000 bytes; choose a smaller upstream window')
    # Exercise the receiving path before returning any package.
    inspect_bytes(data)
    return data


def inspect_bytes(data, expected=None):
    archive = inspector.inspect_stream(io.BytesIO(data), limits=LIMITS, expected=expected)
    names = [entry['path'] for entry in archive['files']]
    if set(names) != {CAPTURE, RECEIPT}:
        raise ValueError('window handoff must contain exactly capture and receipt')
    hazards = portability.analyze(names)
    if hazards:
        raise ValueError('handoff has cross-platform filename hazards')
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        raw = bundle.read(CAPTURE)
        saved = bundle.read(RECEIPT)
    capture = parse(raw)
    recomputed = checked_receipt(capture)
    if saved != canonical(recomputed):
        raise ValueError('saved receipt disagrees with revalidated evidence')
    return {'schema': 'window-handoff/v1', 'verified': True,
            'archive_sha256': archive['archive_sha256'],
            'archive_bytes': archive['archive_bytes'],
            'trusted_digest_matched': archive['trusted_digest_matched'],
            'capture_bytes_sha256': hashlib.sha256(raw).hexdigest(),
            'capture_schema_version': capture['schema_version'],
            'portable_filenames': True, 'receipt_recomputed': True,
            'address_summary_recomputed': 'address_window_summary' in capture,
            'window_receipt': recomputed, 'limitations': NOTE}


def read_file(raw):
    path = handoff.workspace_path(raw)
    return handoff.regular_bytes(path, MAX_BYTES)


def pack(capture, output):
    target = handoff.workspace_path(output, must_exist=False)
    if target.exists():
        raise ValueError('refusing to overwrite existing handoff')
    data = build(read_file(capture))
    result = inspect_bytes(data)
    with target.open('xb') as stream:
        stream.write(data)
    result['output'] = output
    return result


def demo():
    # Exact retained schema-2 public observation, never an invented live result.
    raw = (HERE / 'examples/zto-window.json').read_bytes()
    first = build(raw)
    if first != build(raw):
        raise ValueError('nondeterministic handoff')
    result = inspect_bytes(first)
    result['demo'] = 'retained real ZTO provider observation; no network used'
    result['deterministic'] = True
    return result


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    create = commands.add_parser('pack')
    create.add_argument('capture')
    create.add_argument('output')
    replay = commands.add_parser('inspect')
    replay.add_argument('archive')
    replay.add_argument('--sha256', help='archive digest from an independent trusted channel')
    args = cli.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'pack':
            result = pack(args.capture, args.output)
        else:
            result = inspect_bytes(read_file(args.archive), expected=args.sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, UnicodeError,
            RecursionError, zipfile.BadZipFile, EOFError, NotImplementedError):
        print('window-handoff: invalid, unsupported or inconsistent evidence; no receipt emitted',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
