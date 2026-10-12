#!/usr/bin/env python3
"""Offline regression tests for JSON transaction inspection, with no RPC calls."""
import contextlib
import io
import json
import random
import unittest
from unittest.mock import patch

import rpc_reader as reader


def inspect(obj):
    return reader.inspect_json(json.dumps(obj))["inspection"]


class ReaderTests(unittest.TestCase):
    def test_demo_matches_existing_rlp_inspection(self):
        expected = reader.intent.interpret(reader.D.demo_transaction())
        self.assertEqual(inspect(reader.demo_object()), expected)
        self.assertEqual(expected["destinationLabel"], "ZTO")
        self.assertEqual(expected["calldata"]["candidateMethod"], "totalSupply")
        self.assertEqual(expected["feeBudget"]["gasFeeCapWei"], "200000000000000")

    def test_each_field_required_no_implicit_defaults(self):
        for name in reader.demo_object():
            obj = reader.demo_object()
            del obj[name]
            with self.subTest(field=name), self.assertRaises(ValueError):
                inspect(obj)

    def test_input_alias_and_ambiguous_alias_rejection(self):
        obj = reader.demo_object()
        obj["input"] = obj.pop("data")
        self.assertEqual(inspect(obj), inspect(reader.demo_object()))
        self.assertEqual(reader.inspect_json(json.dumps(obj))["calldataSourceField"], "input")
        for data in (obj["input"], "0x"):
            obj["data"] = data
            with self.assertRaises(ValueError):
                inspect(obj)

    def test_signature_sender_wrapper_and_extra_fields_rejected(self):
        for field in ("r", "s", "v", "yParity", "from", "gasPrice", "hash", "method", "params",
                      "gasLimit", "authorizationList", "maxFeePerBlobGas", "unknown"):
            obj = reader.demo_object()
            obj[field] = None
            with self.subTest(field=field), self.assertRaises(ValueError):
                inspect(obj)
        for kind in ("0x0", "0x1", "0x3", "0x4", "0x02", 2, True):
            obj = reader.demo_object()
            obj["type"] = kind
            with self.assertRaises(ValueError):
                inspect(obj)

    def test_quantities_are_exact_bounded_hex_strings(self):
        bad = (0, True, False, None, [], {}, 1.5, "1", "0X1", "0x", "0x00", "0x01",
               "0x-1", "0x+1", " 0x1", "0x1\n", "0x1_0", "0xg", hex(2**256))
        for name in reader.QUANTITIES:
            for value in bad:
                obj = reader.demo_object()
                obj[name] = value
                with self.subTest(field=name, value=value), self.assertRaises(ValueError):
                    inspect(obj)
        obj = reader.demo_object()
        obj.update(gas=hex(2**256-1), maxFeePerGas=hex(2**256-1), value=hex(2**256-1))
        self.assertEqual(inspect(obj)["feeBudget"]["valuePlusGasFeeCapWei"],
                         str((2**256-1)**2 + (2**256-1)))

    def test_duplicate_keys_rejected_at_every_object_depth(self):
        base = json.dumps(reader.demo_object())
        texts = [base[:-1] + ', "nonce": "0x1"}',
                 base.replace('"accessList": []',
                              '"accessList": [{"address":"' + reader.D.ZTO + '",'
                              '"storageKeys":[],"storageKeys":[]}]'),
                 base[:-1] + ', "\\u006eonce": "0x1"}']
        for text in texts:
            with self.assertRaisesRegex(ValueError, "duplicate"):
                reader.inspect_json(text)

    def test_data_address_and_creation_are_unambiguous(self):
        for field in ("to", "data"):
            for value in ("0X12", "0x1", "0xzz", "0x12 ", [], False):
                obj = reader.demo_object()
                obj[field] = value
                with self.assertRaises(ValueError):
                    inspect(obj)
        obj = reader.demo_object()
        for value in ("0x", "0x12", "0x" + "ab"*21):
            obj["to"] = value
            with self.assertRaises(ValueError):
                inspect(obj)
        obj["to"] = None
        self.assertEqual(inspect(obj)["calldata"]["status"], "contract-creation")
        obj = reader.demo_object()
        obj["data"] = "0x"
        self.assertEqual(inspect(obj)["calldata"]["status"], "empty")
        obj["data"] = "0x18160ddd00"
        self.assertEqual(inspect(obj)["calldata"]["status"], "malformed-known-selector")

    def test_access_list_preserves_order_and_duplicates(self):
        obj = reader.demo_object()
        first = {"address": reader.D.ZTO, "storageKeys": ["0x" + "ab"*32]*2}
        second = {"address": reader.intent.IMD, "storageKeys": []}
        obj["accessList"] = [first, second, first]
        self.assertEqual(inspect(obj)["transaction"]["accessList"], obj["accessList"])
        for value in (None, {}, [None], [[reader.D.ZTO, []]],
                      [{"address": reader.D.ZTO}],
                      [{"address": reader.D.ZTO, "storageKeys": None}],
                      [{"address": reader.D.ZTO, "storageKeys": ["0x01"]}],
                      [{"address": reader.D.ZTO, "storageKeys": [], "extra": None}]):
            obj["accessList"] = value
            with self.assertRaises(ValueError):
                inspect(obj)

    def test_labels_approval_warning_and_fee_order_survive(self):
        obj = reader.demo_object()
        obj["to"] = "0x" + reader.intent.IMD[2:].upper()
        self.assertEqual(inspect(obj)["destinationLabel"], "IMD")
        obj["chainId"] = "0x2"
        self.assertIsNone(inspect(obj)["destinationLabel"])
        obj = reader.demo_object()
        obj["data"] = "0x095ea7b3" + "00"*12 + reader.intent.IMD[2:] + "ff"*32
        obj["maxPriorityFeePerGas"] = "0xffffffffff"
        report = inspect(obj)
        self.assertEqual(report["calldata"]["approvalKind"], "maximum-uint256")
        self.assertIn("Priority fee exceeds maximum fee per gas.", report["warnings"])

    def test_json_limits_malformed_and_non_objects(self):
        for text in ("", "null", "[]", "true", "{} {}", "{", '{"a": NaN}',
                     '{"a": Infinity}', '{"a": -Infinity}', '{"a": 1e100}',
                     "["*2000 + "]"*2000, " "*(reader.MAX_JSON_CHARS+1),
                     '{"a":' + '9'*10000 + '}'):
            with self.subTest(prefix=text[:30]), self.assertRaises(ValueError):
                reader.inspect_json(text)
        obj = reader.demo_object()
        obj["data"] = "0x" + "ab"*reader.D.MAX_TRANSACTION_BYTES
        with self.assertRaisesRegex(ValueError, "128 KiB"):
            inspect(obj)
        # Many empty slot lists fit the JSON bound but exceed the RLP item bound.
        obj = reader.demo_object()
        obj["accessList"] = [{"address": reader.D.ZTO, "storageKeys": []}]*5500
        with self.assertRaisesRegex(ValueError, "item limit"):
            inspect(obj)

    def test_seeded_numeric_roundtrips_against_independent_expected_values(self):
        rng = random.Random(26)
        for _ in range(150):
            obj = reader.demo_object()
            expected = {name: rng.getrandbits(rng.randrange(257)) for name in reader.QUANTITIES}
            obj.update({name: hex(value) for name, value in expected.items()})
            tx = inspect(obj)["transaction"]
            for name, value in expected.items():
                self.assertEqual(tx["gasLimit" if name == "gas" else name], str(value))

    def test_cli_modes_exit_codes_and_no_partial_output(self):
        for args in (["--demo"], [json.dumps(reader.demo_object())], ["--stdin"]):
            with patch("sys.stdin", io.StringIO(json.dumps(reader.demo_object()))), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(reader.main(args), 0)
            self.assertEqual(json.loads(output.getvalue())["inspection"]["destinationLabel"], "ZTO")
        for args in ([], ["--demo", "extra"], ["--other"], ['{"nonce":true}'], ["{"], ["--stdin"]):
            with patch("sys.stdin", io.StringIO(" "*(reader.MAX_JSON_CHARS+1))), \
                    contextlib.redirect_stdout(io.StringIO()) as output, \
                    contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(reader.main(args), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertNotIn("Traceback", errors.getvalue())
            self.assertTrue(errors.getvalue())


if __name__ == "__main__":
    unittest.main()
