"""Frame order of the event corpus (amendment A1, prereg/AMENDMENT_LOG.md; checklist B10(b')).
The tests on real data skip when the detection dump or the LASIESTA frames are not present."""
import glob
import json
import os
import re

import pytest

from sim40 import config as cfg
from sim40.events import _events_from_frames, lasiesta_frame_numbers, temporal_frames

LAS_FRAMES = cfg.DS / "LASIESTA"
LAS_DUMP = cfg.DET / "LASIESTA"


def _frames(active_numbers, n):
    """A dump as the pipeline writes it: index = position in the text-sorted list of names 1..n."""
    nums = lasiesta_frame_numbers(n)
    return [{"frame": i, "boxes": [[0, 0, 1, 1, 0.9, 0]] if num in active_numbers else []} for i, num in enumerate(nums)]


def test_text_order_of_names():
    assert lasiesta_frame_numbers(12) == [1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9]
    assert lasiesta_frame_numbers(3) == [1, 2, 3]            # below 10, text order = time
    nums = lasiesta_frame_numbers(275)
    assert nums[:5] == [1, 10, 100, 101, 102] and sorted(nums) == list(range(1, 276))


def test_one_run_in_time_is_one_event():
    """Numbers 9, 10, 11 are consecutive in time but sit at text positions 11, 1, 2."""
    frames = _frames({9, 10, 11}, 12)
    assert [f["frame"] for f in frames if f["boxes"]] == [1, 2, 11]
    assert len(_events_from_frames(frames)) == 2             # the dump index cuts it in two
    assert _events_from_frames(temporal_frames("LASIESTA", frames)) == [(8, 3)]


def test_event_at_the_end_of_a_sequence():
    assert _events_from_frames(temporal_frames("LASIESTA", _frames({11, 12}, 12))) == [(10, 2)]


def test_other_datasets_are_not_reordered():
    frames = _frames({9, 10, 11}, 12)
    assert temporal_frames("CDnet2014", frames) is frames
    assert temporal_frames("BMC", frames) is frames


def _load(seq):
    f = next(iter(LAS_DUMP.glob(f"*__{seq}.json")), None)
    if f is None:
        pytest.skip("LASIESTA detection dump not present")
    return json.loads(f.read_text(encoding="utf-8"))["frames"]


@pytest.mark.parametrize("seq, expected_time, n_events_index", [
    # hand check 07-11-2026: frames written in file-number order and read off by eye, I_OC_02: 87 empty, 49 active,
    # 24 empty, 89 active, 1 empty = 250 frames. The dump index cuts the same frames into 15 events.
    ("I_OC_02", [(87, 49), (160, 89)], 15),
    ("I_BS_01", [(0, 174)], 12),
])
def test_hand_checked_sequence(seq, expected_time, n_events_index):
    frames = _load(seq)
    assert _events_from_frames(temporal_frames("LASIESTA", frames)) == expected_time
    assert len(_events_from_frames(frames)) == n_events_index


def test_map_matches_the_real_file_names():
    """Our generated map equals the numbers read from the real text-sorted file names, on every sequence."""
    if not LAS_FRAMES.exists() or not LAS_DUMP.exists():
        pytest.skip("LASIESTA frames or dump not present")
    n_seq = 0
    for f in sorted(LAS_DUMP.glob("*.json")):
        seq = f.stem.split("__", 1)[1]
        names = sorted(glob.glob(os.path.join(LAS_FRAMES, seq, "*.bmp")))
        real = [int(re.search(r"-(\d+)\.bmp$", p).group(1)) for p in names]
        assert real == lasiesta_frame_numbers(len(json.loads(f.read_text(encoding="utf-8"))["frames"])), seq
        n_seq += 1
    assert n_seq == 48
