import math

# 尺寸单位：mm
DIAMETER = 25.0
VERTICAL_HEIGHT = 100.0
TILT_FROM_VERTICAL_DEG = 30.0
AZIMUTH_WEST_OF_NORTH_DEG = 45.0
SIDES = 128
OUTPUT_FILE = "tilted_cylinder.stl"


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize(v):
    length = math.sqrt(dot(v, v))
    return tuple(x / length for x in v)


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def write_facet(file, a, b, c):
    normal = normalize(cross(subtract(b, a), subtract(c, a)))

    file.write(f"  facet normal {normal[0]:.9g} {normal[1]:.9g} {normal[2]:.9g}\n")
    file.write("    outer loop\n")
    for p in (a, b, c):
        file.write(f"      vertex {p[0]:.9g} {p[1]:.9g} {p[2]:.9g}\n")
    file.write("    endloop\n")
    file.write("  endfacet\n")


def main():
    radius = DIAMETER / 2.0
    tilt = math.radians(TILT_FROM_VERTICAL_DEG)
    azimuth = math.radians(AZIMUTH_WEST_OF_NORTH_DEG)

    # 坐标约定：X=东，Y=北，Z=上。
    # “北偏西45°”的水平分量：X为负，Y为正。
    axis = (
        -math.sin(azimuth) * math.sin(tilt),
         math.cos(azimuth) * math.sin(tilt),
         math.cos(tilt),
    )

    # 由竖直投影高度计算圆柱轴向长度。
    length = VERTICAL_HEIGHT / axis[2]

    # 构造垂直于圆柱轴线的两个单位向量，用于生成圆周。
    reference = (0.0, 0.0, 1.0)
    u = normalize(cross(reference, axis))
    v = normalize(cross(axis, u))

    bottom_center = (0.0, 0.0, 0.0)
    top_center = tuple(length * component for component in axis)

    bottom_ring = []
    top_ring = []

    for i in range(SIDES):
        angle = 2.0 * math.pi * i / SIDES
        radial = tuple(
            radius * (math.cos(angle) * u[j] + math.sin(angle) * v[j])
            for j in range(3)
        )
        bottom_ring.append(tuple(bottom_center[j] + radial[j] for j in range(3)))
        top_ring.append(tuple(top_center[j] + radial[j] for j in range(3)))

    with open(OUTPUT_FILE, "w", encoding="ascii") as f:
        f.write("solid tilted_cylinder\n")

        for i in range(SIDES):
            j = (i + 1) % SIDES

            # 圆柱侧面，拆分成两个三角形
            write_facet(f, bottom_ring[i], bottom_ring[j], top_ring[j])
            write_facet(f, bottom_ring[i], top_ring[j], top_ring[i])

            # 下端盖
            write_facet(f, bottom_center, bottom_ring[j], bottom_ring[i])

            # 上端盖
            write_facet(f, top_center, top_ring[i], top_ring[j])

        f.write("endsolid tilted_cylinder\n")

    print(f"已生成：{OUTPUT_FILE}")
    print(f"圆柱轴向长度：{length:.6f} mm")
    print(f"竖直投影高度：{top_center[2]:.6f} mm")
    print(f"网格圆周分段数：{SIDES}")


if __name__ == "__main__":
    main()