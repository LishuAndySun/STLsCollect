import math

# 尺寸，单位：mm
DIAMETER = 22.0
LEG1 = 50.0
LEG2 = 62.73
BEND_RADIUS = 25.0

# 网格精度：圆周分段数和弯曲段分段数
CIRCLE_SEGMENTS = 48
ARC_SEGMENTS = 48
STRAIGHT_STEP = 2.0

TUBE_RADIUS = DIAMETER / 2.0


def centerline_points():
    """生成中心线点：第一段沿 +X，90°转弯后沿 +Z。"""
    points = []

    # 第一段直线，包含弯曲起点
    n = max(1, math.ceil(LEG1 / STRAIGHT_STEP))
    for i in range(n + 1):
        x = LEG1 * i / n
        points.append((x, 0.0, 0.0))

    # 90°圆弧，起点已包含在第一段中
    for i in range(1, ARC_SEGMENTS + 1):
        a = (math.pi / 2.0) * i / ARC_SEGMENTS
        points.append((
            LEG1 + BEND_RADIUS * math.sin(a),
            0.0,
            BEND_RADIUS * (1.0 - math.cos(a)),
        ))

    # 第二段直线，从弯曲终点继续延伸
    n = max(1, math.ceil(LEG2 / STRAIGHT_STEP))
    for i in range(1, n + 1):
        z = BEND_RADIUS + LEG2 * i / n
        points.append((LEG1 + BEND_RADIUS, 0.0, z))

    return points


def subtract(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize(v):
    length = math.sqrt(dot(v, v))
    if length == 0:
        raise ValueError("中心线出现重复点")
    return scale(v, 1.0 / length)


def make_rings(points):
    """沿中心线生成圆形截面顶点。"""
    rings = []

    for i, p in enumerate(points):
        if i == 0:
            tangent = normalize(subtract(points[1], points[0]))
        elif i == len(points) - 1:
            tangent = normalize(subtract(points[-1], points[-2]))
        else:
            tangent = normalize(subtract(points[i + 1], points[i - 1]))

        # 构造垂直于切线的截面基向量
        ref = (0.0, 1.0, 0.0)
        u = normalize(cross(tangent, ref))
        v = normalize(cross(tangent, u))

        ring = []
        for j in range(CIRCLE_SEGMENTS):
            angle = 2.0 * math.pi * j / CIRCLE_SEGMENTS
            offset = add(
                scale(u, TUBE_RADIUS * math.cos(angle)),
                scale(v, TUBE_RADIUS * math.sin(angle)),
            )
            ring.append(add(p, offset))
        rings.append(ring)

    return rings


def normal(a, b, c):
    return normalize(cross(subtract(b, a), subtract(c, a)))


def write_triangle(file, a, b, c):
    n = normal(a, b, c)
    file.write(f"  facet normal {n[0]:.7g} {n[1]:.7g} {n[2]:.7g}\n")
    file.write("    outer loop\n")
    for p in (a, b, c):
        file.write(f"      vertex {p[0]:.7g} {p[1]:.7g} {p[2]:.7g}\n")
    file.write("    endloop\n")
    file.write("  endfacet\n")


def generate_stl(filename):
    points = centerline_points()
    rings = make_rings(points)

    with open(filename, "w", encoding="ascii") as f:
        f.write("solid solid_90deg_elbow\n")

        # 侧面三角网格
        for i in range(len(rings) - 1):
            for j in range(CIRCLE_SEGMENTS):
                j2 = (j + 1) % CIRCLE_SEGMENTS

                a = rings[i][j]
                b = rings[i][j2]
                c = rings[i + 1][j]
                d = rings[i + 1][j2]

                write_triangle(f, a, b, c)
                write_triangle(f, b, d, c)

        # 两端封口：中心点扇形三角面
        start_center = points[0]
        end_center = points[-1]

        for j in range(CIRCLE_SEGMENTS):
            j2 = (j + 1) % CIRCLE_SEGMENTS

            # 起始端盖
            write_triangle(f, start_center, rings[0][j2], rings[0][j])

            # 末端端盖
            write_triangle(
                f,
                end_center,
                rings[-1][j],
                rings[-1][j2],
            )

        f.write("endsolid solid_90deg_elbow\n")


if __name__ == "__main__":
    output = "solid_90deg_pipe.stl"
    generate_stl(output)
    print(f"已生成：{output}")