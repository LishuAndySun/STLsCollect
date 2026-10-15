#!/usr/bin/env python3
"""
不使用 NumPy 的 GLB 解析器

用法：
    python glb_info_nonumpy.py model.glb

功能：
- 解析 GLB 头部与 JSON / BIN 数据块
- 报告场景、节点、网格数量
- 读取每个网格的 POSITION 访问器，计算局部包围盒
- 报告节点层次以及节点的平移/缩放

注意：
- 该脚本读取的是网格自身的顶点坐标，并叠加节点的平移与缩放。
  它不处理复杂的旋转、矩阵或蒙皮，也不做坐标系转换。
- 不同软件导出的 GLB 单位可能不同，需要结合已知尺寸核对。
"""

import base64
import json
import struct
import sys
from pathlib import Path

# 访问器 componentType 对应 struct 格式与字节数
COMPONENT_TYPES = {
    5120: ("b", 1),  # BYTE
    5121: ("B", 1),  # UNSIGNED_BYTE
    5122: ("h", 2),  # SHORT
    5123: ("H", 2),  # UNSIGNED_SHORT
    5125: ("I", 4),  # UNSIGNED_INT
    5126: ("f", 4),  # FLOAT
}

TYPE_COUNTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}

def read_glb(path):
    data = Path(path).read_bytes()

    if len(data) < 12:
        raise ValueError("文件过小，不是有效的 GLB。")

    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:  # 'glTF'
        raise ValueError("文件头不是 glTF 标志，可能是 .gltf 或损坏文件。")

    print(f"GLB 版本：{version}")
    print(f"文件声明长度：{length} 字节，实际读取：{len(data)} 字节")

    json_chunk = None
    bin_chunk = None
    offset = 12

    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk_data = data[offset:offset + chunk_length]
        offset += chunk_length

        if chunk_type == 0x4E4F534A:  # 'JSON'
            json_chunk = chunk_data
        elif chunk_type == 0x004E4942:  # 'BIN'
            bin_chunk = chunk_data

    if json_chunk is None:
        raise ValueError("没有找到 JSON 数据块。")

    return json.loads(json_chunk.decode("utf-8")), bin_chunk

def get_accessor_values(gltf, bin_chunk, accessor_index):
    accessor = gltf["accessors"][accessor_index]
    component_type = accessor["componentType"]
    type_count = TYPE_COUNTS[accessor["type"]]
    count = accessor["count"]

    if component_type not in COMPONENT_TYPES:
        raise ValueError(f"暂不支持的 componentType：{component_type}")

    fmt, size = COMPONENT_TYPES[component_type]
    values = []

    if "bufferView" in accessor:
        buffer_view = gltf["bufferViews"][accessor["bufferView"]]
        buffer_index = buffer_view.get("buffer", 0)

        if buffer_index != 0 or bin_chunk is None:
            raise ValueError("该访问器指向的数据不在内嵌 BIN 块中。")

        byte_offset = buffer_view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = buffer_view.get("byteStride")
        element_size = size * type_count

        for i in range(count):
            start = byte_offset + (i * stride if stride else i * element_size)
            chunk = bin_chunk[start:start + element_size]
            values.append(struct.unpack_from("<" + fmt * type_count, chunk, 0))
    else:
        # 可选：访问器直接内嵌数据（少见）
        raise ValueError("访问器没有 bufferView，暂不支持。")

    return values, type_count

def node_local_transform(node):
    """只处理平移与缩放，忽略旋转。"""
    if "matrix" in node:
        return None  # 含矩阵时本脚本不计算

    translation = node.get("translation", [0.0, 0.0, 0.0])
    scale = node.get("scale", [1.0, 1.0, 1.0])
    return translation, scale

def collect_meshes(gltf):
    """按网格统计，不完整处理节点层次变换。"""
    results = []

    for mesh_index, mesh in enumerate(gltf.get("meshes", [])):
        mesh_name = mesh.get("name", f"mesh_{mesh_index}")
        mins = [float("inf")] * 3
        maxs = [float("-inf")] * 3
        vertex_total = 0

        for primitive in mesh.get("primitives", []):
            position_index = primitive.get("attributes", {}).get("POSITION")
            if position_index is None:
                continue
            values, _ = get_accessor_values(gltf, gltf["_bin"], position_index)
            vertex_total += len(values)

            for vertex in values:
                for axis in range(3):
                    mins[axis] = min(mins[axis], vertex[axis])
                    maxs[axis] = max(maxs[axis], vertex[axis])

        if vertex_total == 0:
            continue

        size = [maxs[i] - mins[i] for i in range(3)]
        results.append((mesh_name, vertex_total, mins, maxs, size))

    return results

def main():
    if len(sys.argv) != 2:
        print("用法：python glb_info_nonumpy.py 文件名.glb")
        raise SystemExit(2)

    path = Path(sys.argv[1])
    if not path.is_file():
        raise SystemExit(f"找不到文件：{path}")

    try:
        gltf, bin_chunk = read_glb(path)
    except Exception as exc:
        raise SystemExit(f"解析失败：{exc}")

    gltf["_bin"] = bin_chunk

    print(f"\n文件：{path.name}")
    print(f"场景数：{len(gltf.get('scenes', []))}")
    print(f"节点数：{len(gltf.get('nodes', []))}")
    print(f"网格数：{len(gltf.get('meshes', []))}")

    print("\n=== 各网格局部包围盒（未叠加节点变换）===")
    for name, vertex_total, mins, maxs, size in collect_meshes(gltf):
        print(f"\n网格：{name}")
        print(f"  顶点数：{vertex_total}")
        for axis in range(3):
            label = "XYZ"[axis]
            print(
                f"  {label}: {mins[axis]:.3f} 到 {maxs[axis]:.3f}，"
                f"尺寸 {size[axis]:.3f}"
            )

    print("\n=== 节点结构 ===")
    for index, node in enumerate(gltf.get("nodes", [])):
        name = node.get("name", f"node_{index}")
        has_mesh = "mesh" in node
        children = node.get("children", [])
        transform = node_local_transform(node)
        print(f"\n节点 {index}：{name}")
        if has_mesh:
            print(f"  使用网格：{node['mesh']}")
        if children:
            print(f"  子节点：{children}")
        if transform is not None:
            translation, scale = transform
            print(f"  平移：{translation}")
            print(f"  缩放：{scale}")
        if "matrix" in node:
            print("  含矩阵变换（本脚本未计算）")

    print("\n注意：本脚本不处理旋转、矩阵和蒙皮，且 GLB 单位需结合已知尺寸核对。")

if __name__ == "__main__":
    main()