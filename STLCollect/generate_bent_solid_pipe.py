import math
import struct
from pathlib import Path

# Dimensions in millimetres.
DIAMETER = 22.0
CENTERLINE_RADIUS = 25.0
FIRST_STRAIGHT = 83.0
SECOND_STRAIGHT = 120.0
CIRCUMFERENCE_SEGMENTS = 96
ARC_SEGMENTS = 96
OUTPUT = Path(__file__).with_name("solid_bent_pipe_22mm_83x120_R25.stl")


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(vector, amount):
    return tuple(value * amount for value in vector)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normal(a, b, c):
    edge_a = tuple(b[i] - a[i] for i in range(3))
    edge_b = tuple(c[i] - a[i] for i in range(3))
    vector = cross(edge_a, edge_b)
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return (0.0, 0.0, 0.0)
    return scale(vector, 1.0 / length)


def centerline_samples():
    samples = []

    for index in range(ARC_SEGMENTS + 1):
        fraction = index / ARC_SEGMENTS
        samples.append((FIRST_STRAIGHT * fraction, 0.0, (1.0, 0.0, 0.0)))

    for index in range(1, ARC_SEGMENTS + 1):
        angle = -math.pi / 2.0 + (math.pi / 2.0) * index / ARC_SEGMENTS
        center = (FIRST_STRAIGHT, CENTERLINE_RADIUS, 0.0)
        point = (
            center[0] + CENTERLINE_RADIUS * math.cos(angle),
            center[1] + CENTERLINE_RADIUS * math.sin(angle),
            0.0,
        )
        tangent = (-math.sin(angle), math.cos(angle), 0.0)
        samples.append((point[0], point[1], tangent))

    arc_end = (FIRST_STRAIGHT + CENTERLINE_RADIUS, CENTERLINE_RADIUS, 0.0)
    for index in range(1, ARC_SEGMENTS + 1):
        fraction = index / ARC_SEGMENTS
        point = (arc_end[0], arc_end[1] + SECOND_STRAIGHT * fraction, 0.0)
        samples.append((point[0], point[1], (0.0, 1.0, 0.0)))

    return samples


def make_mesh():
    radius = DIAMETER / 2.0
    samples = centerline_samples()
    rings = []

    for x, y, tangent in samples:
        left_normal = (-tangent[1], tangent[0], 0.0)
        binormal = (0.0, 0.0, 1.0)
        ring = []
        for index in range(CIRCUMFERENCE_SEGMENTS):
            angle = 2.0 * math.pi * index / CIRCUMFERENCE_SEGMENTS
            offset = add(
                scale(left_normal, radius * math.cos(angle)),
                scale(binormal, radius * math.sin(angle)),
            )
            ring.append((x + offset[0], y + offset[1], offset[2]))
        rings.append(ring)

    triangles = []
    for ring_index in range(len(rings) - 1):
        current = rings[ring_index]
        following = rings[ring_index + 1]
        for segment in range(CIRCUMFERENCE_SEGMENTS):
            next_segment = (segment + 1) % CIRCUMFERENCE_SEGMENTS
            triangles.append((current[segment], following[segment], following[next_segment]))
            triangles.append((current[segment], following[next_segment], current[next_segment]))

    start_center = samples[0][:2] + (0.0,)
    end_center = samples[-1][:2] + (0.0,)
    for segment in range(CIRCUMFERENCE_SEGMENTS):
        next_segment = (segment + 1) % CIRCUMFERENCE_SEGMENTS
        triangles.append((start_center, rings[0][next_segment], rings[0][segment]))
        triangles.append((end_center, rings[-1][segment], rings[-1][next_segment]))

    return triangles


def write_binary_stl(triangles):
    header = b"Solid bent solid pipe generated in millimetres"
    header = header.ljust(80, b" ")
    with OUTPUT.open("wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(triangles)))
        for triangle in triangles:
            handle.write(struct.pack("<3f", *normal(*triangle)))
            for vertex in triangle:
                handle.write(struct.pack("<3f", *vertex))
            handle.write(struct.pack("<H", 0))


if __name__ == "__main__":
    mesh = make_mesh()
    write_binary_stl(mesh)
    print(f"Wrote {OUTPUT.name}: {len(mesh)} triangles")
    print("Overall centerline end-to-end length: "
          f"{FIRST_STRAIGHT + math.pi * CENTERLINE_RADIUS / 2.0 + SECOND_STRAIGHT:.3f} mm")
