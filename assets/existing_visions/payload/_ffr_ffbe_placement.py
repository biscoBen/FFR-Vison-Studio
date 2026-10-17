"""Audited adapter for BMB ordered-model generation (development converter).

Memorial arm64 libgame.so: NullEmitterNode::Initialize selects shape at +0xA8;
generate_shape::ModuleParamTable<Null>::InitModuleOf slot 8 calls
InitModelOnOrderedVertex (0x1FBE8D8). Model::OnIndexedVertexPosition
(0x1FEA144) takes ordinal modulo vertex count and multiplies XYZ by +0x148.
All descendants of an emitted node share that node's ordinal and position.
Other nonzero shape modes are rejected rather than silently superimposed.
"""
from pathlib import Path
import struct


def install(ibmb):
    if getattr(ibmb, '_ffr_ordered_model_placement', False):
        return
    ibmb._ffr_ordered_model_placement = True
    original_parse, original_transform = ibmb.parse, ibmb._node_transform

    def parse(path):
        effect = original_parse(path)
        raw = Path(path).read_bytes()
        for node in effect.chunks:
            if not node.is_node:
                continue
            mode = struct.unpack_from('<I', raw, node.offset + 0xA8)[0]
            if mode == 0:
                continue
            if mode != 8 or raw[node.offset + 0x6D]:
                raise ValueError(f'Unsupported BMB generation shape/alignment: node {node.index}, mode {mode}')
            # NullEmitterNode resolves its positioning model from resource +0x30.
            offset = struct.unpack_from('<I', raw, node.offset + 0x30)[0]
            reader = ibmb._Reader(raw)
            resource = reader.string(offset)
            model = Path(path).with_name(str(resource) + '.m3r')
            if not resource or not model.is_file():
                raise ValueError('Missing BMB positioning mesh: ' + str(resource))
            vertices = ibmb.parse_m3r(str(model))['vertices']
            if not vertices:
                raise ValueError('Empty BMB positioning mesh: ' + resource)
            node._position_vertices = vertices
            node._position_scale = struct.unpack_from('<3f', raw, node.offset + 0x148)
        return effect

    def transform(chain, frame, effect_dur, instance_starts=None,
                  translation_cache=None, return_matrix=False, variation=None,
                  instance_keys=None, copy_index=0):
        result = original_transform(chain, frame, effect_dur, instance_starts,
                                    translation_cache, return_matrix, variation, instance_keys, copy_index)
        for i, node in enumerate(chain):
            vertices = getattr(node, '_position_vertices', None)
            if vertices is None:
                continue
            if instance_keys is None:
                raise ValueError('Model placement requires the native per-node emission ordinal')
            vertex = vertices[instance_keys[i] % len(vertices)]
            local = [a*b for a, b in zip(vertex, node._position_scale)]
            parent = original_transform(chain[:i], frame, effect_dur,
                instance_starts[:i] if instance_starts is not None else None,
                translation_cache, True, variation, instance_keys[:i], copy_index)[-1]
            placed = ibmb._point_in_frame(parent, local)
            for axis in range(3):
                result[0][axis] += placed[axis]
        return result

    ibmb.parse, ibmb._node_transform = parse, transform
