import math

# 尺寸单位：mm
DIAMETER = 25.0
HEIGHT = 100.0
TILT_FROM_VERTICAL_DEG = 30.0
AZIMUTH_WEST_OF_NORTH_DEG = 45.0
SIDES = 256
OUTPUT_FILE = "tilted_cylinder.stl"


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def normalize(v):
    length = math.sqrt(sum(x * x for x in v))
    if length == 0:
        raise ValueError("无法将零向量归一化")
    return tuple(x / length for x in v)


def write_facet(file, a, b, c):
    normal = normalize(cross(subtract(b, a), subtract(c, a)))

    file.write(
        f"  facet normal {normal[0]:.9g} "
        f"{normal[1]:.9g} {normal[2]:.9g}\n"
    )
    file.write("    outer loop\n")
    for point in (a, b, c):
        file.write(
            f"      vertex {point[0]:.9g} "
            f"{point[1]:.9g} {point[2]:.9g}\n"
        )
    file.write("    endloop\n")
    file.write("  endfacet\n")


def main():
    radius = DIAMETER / 2.0
    tilt = math.radians(TILT_FROM_VERTICAL_DEG)
    azimuth = math.radians(AZIMUTH_WEST_OF_NORTH_DEG)

    # 轴线的水平位移由倾角和高度确定。
    # 坐标约定：X=东，Y=北，Z=上。
    center_shift_x = -HEIGHT * math.tan(tilt) * math.sin(azimuth)
    center_shift_y =  HEIGHT * math.tan(tilt) * math.cos(azimuth)

    # 上下两个端面都在水平面内，是相同大小、相同朝向的圆。
    bottom_ring = []
    top_ring = []

    for i in range(SIDES):
        angle = 2.0 * math.pi * i / SIDES
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        bottom_ring.append((x, y, 0.0))
        top_ring.append((x + center_shift_x, y + center_shift_y, HEIGHT))

    bottom_center = (0.0, 0.0, 0.0)
    top_center = (center_shift_x, center_shift_y, HEIGHT)

    with open(OUTPUT_FILE, "w", encoding="ascii") as f:
        f.write("solid tilted_cylinder_with_horizontal_ends\n")

        for i in range(SIDES):
            j = (i + 1) % SIDES

            # 侧壁：连接上下圆周对应的顶点
            write_facet(f, bottom_ring[i], bottom_ring[j], top_ring[j])
            write_facet(f, bottom_ring[i], top_ring[j], top_ring[i])

            # 底面法线朝下
            write_facet(f, bottom_center, bottom_ring[j], bottom_ring[i])

            # 顶面法线朝上
            write_facet(f, top_center, top_ring[i], top_ring[j])

        f.write("endsolid tilted_cylinder_with_horizontal_ends\n")

    print(f"已生成：{OUTPUT_FILE}")
    print(f"底面与顶面直径：{DIAMETER:.3f} mm")
    print(f"底面到顶面的竖直距离：{HEIGHT:.3f} mm")
    print(f"中心轴线倾角：{TILT_FROM_VERTICAL_DEG:.3f}°（相对竖直方向）")
    print(
        "中心轴线水平偏移："
        f"X={center_shift_x:.3f} mm，Y={center_shift_y:.3f} mm"
    )
    print("注意：这是两端面平行于地面的斜柱体，端面不垂直于轴线。")


if __name__ == "__main__":
    main()