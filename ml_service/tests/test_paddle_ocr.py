import json

import numpy as np
import pytest

import paddle_ocr


def paddle_lines():
    return [[[
        [[10, 20], [100, 20], [100, 50], [10, 50]],
        ("MRP Rs 120", np.float32(0.94))
    ]]]


def test_normalize_paddle_result_matches_common_contract():
    result = paddle_ocr.normalize_paddle_result(paddle_lines())

    assert result["success"] is True
    assert result["full_text"] == "MRP Rs 120"
    block = result["text_blocks"][0]
    assert block["text"] == "MRP Rs 120"
    assert block["confidence"] == pytest.approx(0.94)
    assert block["box"] == [[10, 20], [100, 20], [100, 50], [10, 50]]
    json.dumps(result)


def test_normalize_paddle_result_handles_empty_output():
    result = paddle_ocr.normalize_paddle_result([])

    assert result["success"] is True
    assert result["full_text"] == ""
    assert result["text_blocks"] == []


def test_normalize_paddle_result_skips_malformed_evidence():
    result = paddle_ocr.normalize_paddle_result([
        [["not a box", ("fabricated", 0.99)]],
        [[[[1, 2], [3, 2], [3, 4]], ("missing point", 0.9)]],
        [[[[1, 2], [3, 2], [3, 4], [1, 4]], ("bad confidence", "unknown")]]
    ])

    assert result["success"] is True
    assert result["text_blocks"] == []
    assert result["full_text"] == ""


def test_extract_text_uses_injected_reader_and_handles_empty_image(tmp_path):
    image_path = tmp_path / "blank.jpg"
    image_path.write_bytes(b"not an image")

    class Reader:
        def ocr(self, image, cls):
            raise AssertionError("corrupt images must not reach the reader")

    result = paddle_ocr.extract_text(str(image_path), reader=Reader())

    assert result["success"] is False
    assert result["error"] == "CORRUPT_IMAGE"