import math

# 所有尺寸单位均为 mm
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
    if length == 0:
        raise ValueError("无法将零向量归一化")
    return tuple(x / length for x in v)


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def write_facet(file, a, b, c):
    normal = normalize(cross(subtract(b, a), subtract(c, a)))

    file.write(
        f"  facet normal {normal[0]:.9g} "
        f"{normal[1]:.9g} {normal[2]:.9g}\n"
    )
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
    # 轴线水平投影为北偏西45°。
    axis = normalize((
        -math.sin(azimuth) * math.sin(tilt),
         math.cos(azimuth) * math.sin(tilt),
         math.cos(tilt),
    ))

    # 输入的是竖直投影高度，因此按轴线的 Z 分量计算实际长度。
    axis_length = VERTICAL_HEIGHT / axis[2]

    bottom_center = (0.0, 0.0, 0.0)
    top_center = tuple(axis_length * component for component in axis)

    # u、v 均垂直于轴线，构成圆形端面的平面基底。
    reference = (0.0, 0.0, 1.0)
    u = normalize(cross(reference, axis))
    v = normalize(cross(axis, u))

    bottom_ring = []
    top_ring = []

    for i in range(SIDES):
        angle = 2.0 * math.pi * i / SIDES

        radial = tuple(
            radius * (
                math.cos(angle) * u[j] +
                math.sin(angle) * v[j]
            )
            for j in range(3)
        )

        bottom_ring.append(tuple(
            bottom_center[j] + radial[j] for j in range(3)
        ))
        top_ring.append(tuple(
            top_center[j] + radial[j] for j in range(3)
        ))

    with open(OUTPUT_FILE, "w", encoding="ascii") as f:
        f.write("solid tilted_cylinder\n")

        for i in range(SIDES):
            j = (i + 1) % SIDES

            # 侧面三角形，法线朝圆柱外侧
            write_facet(f, bottom_ring[i], top_ring[i], top_ring[j])
            write_facet(f, bottom_ring[i], top_ring[j], bottom_ring[j])

            # 下端面，法线朝 -axis
            write_facet(f, bottom_center, bottom_ring[i], bottom_ring[j])

            # 上端面，法线朝 +axis
            write_facet(f, top_center, top_ring[j], top_ring[i])

        f.write("endsolid tilted_cylinder\n")

    print(f"STL 文件已生成：{OUTPUT_FILE}")
    print(f"直径：{DIAMETER:.3f} mm")
    print(f"轴向长度：{axis_length:.6f} mm")
    print(f"竖直投影高度：{top_center[2]:.6f} mm")
    print(f"圆周分段数：{SIDES}")


if __name__ == "__main__":
    main()