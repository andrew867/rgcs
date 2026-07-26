import json

from hypothesis import given, strategies as st

from rgcs_lab.golay import decode_address, decode_block, demo, encode_address, encode_block


@given(st.integers(min_value=0, max_value=4095))
def test_golay_block_corrects_up_to_three_flips(data):
    code = encode_block(data)
    for mask in (0, 1, 0b101, (1 << 23) | (1 << 7) | 1):
        out = decode_block(code ^ mask)
        assert out.decoded == data
        assert out.status in {"OK", "CORRECTED"}


def test_golay_address_receipt_and_four_flip_boundary():
    rec = demo(165876523, [0, 1, 2])
    assert rec["status"] == "GREEN"
    assert rec["result"]["decoded_address"] == 165876523
    assert json.dumps(rec)
    bad = decode_address(encode_address(165876523) ^ 0b1111)
    assert bad["exact_round_trip"] is False

