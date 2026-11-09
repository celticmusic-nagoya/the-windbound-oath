#!/usr/bin/env python3
"""Unit tests for the non-mutating Phase 2 height asset preflight."""
import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "tools/field/check_height_assets.py"
spec = importlib.util.spec_from_file_location("check_height_assets", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def png(width, height, color=6, depth=8):
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xffffffff)
    pixel = b"\\x00" + (b"\\x00" * (width * (4 if color == 6 else 3)))
    raw = pixel * height
    return (bytes([137,80,78,71,13,10,26,10]) +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, depth, color, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

class HeightAssetPreflightTests(unittest.TestCase):
    def test_duplicate_id_against_visuals(self):
        errors = mod.validate_pieces({"visuals":[{"id":"same"}], "pieces":[{"id":"same","anchor":[1,2]}]})
        self.assertTrue(any("duplicate id" in e for e in errors))
    def test_duplicate_piece_ids(self):
        errors = mod.validate_pieces({"pieces":[{"id":"same","anchor":[1,2]},{"id":"same","anchor":[3,4]}]})
        self.assertTrue(any("duplicate id" in e for e in errors))
    def test_valid_piece(self):
        self.assertEqual(mod.validate_pieces({"pieces":[{"id":"rock","anchor":[1,2]}]}), [])
    def test_invalid_anchor(self):
        self.assertTrue(mod.validate_pieces({"pieces":[{"id":"rock","anchor":[1]}]}))
    def test_rgba_dimensions(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"rock.png"
            path.write_bytes(png(160,112))
            self.assertEqual(mod.validate_png(path,(160,112)),[])
            self.assertTrue(any("expected" in e for e in mod.validate_png(path,(280,300))))
    def test_rgb_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"rgb.png"
            path.write_bytes(png(160,112,color=2))
            self.assertTrue(any("RGBA" in e for e in mod.validate_png(path,(160,112))))
    def test_invalid_signature(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"bad.png"
            path.write_bytes(b"not a png")
            self.assertTrue(mod.validate_png(path,(160,112)))

if __name__ == "__main__":
    unittest.main()
