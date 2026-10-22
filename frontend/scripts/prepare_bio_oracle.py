"""Combine cropped Bio-ORACLE CSV0 downloads into the checked-in teaching grid."""

import argparse
import csv
import math
from pathlib import Path


def read_grid(path: Path) -> dict[tuple[float, float], float]:
    result = {}
    with path.open(newline="") as source:
        for time, latitude, longitude, value in csv.reader(source):
            number = float(value)
            if math.isfinite(number):
                key = (float(latitude), float(longitude))
                if key in result:
                    raise ValueError(f"duplicate grid cell in {path}: {key}")
                result[key] = number
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("future", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    baseline = read_grid(args.baseline)
    future = read_grid(args.future)
    if baseline.keys() != future.keys():
        raise ValueError("baseline and future ocean cells differ")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(("latitude", "longitude", "baseline_c", "ssp245_2050_c"))
        for latitude, longitude in sorted(baseline):
            key = (latitude, longitude)
            writer.writerow((latitude, longitude, round(baseline[key], 3), round(future[key], 3)))


if __name__ == "__main__":
    main()
