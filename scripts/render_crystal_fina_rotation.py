"""Blender 4.3 scene for the local intact-crystal cinematic revision.

The crystal is a rotating 3D mesh. Fina is an illustrated, stationary layer;
only her eye region blends to the approved red-eyed awakening layer.
Run with blender -b --python this_file.py -- --output DIR [--frames 1,96,192].
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
FPS, FRAMES = 30, 192


def material(name):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    result.node_tree.nodes.clear()
    return result, result.node_tree.nodes, result.node_tree.links


def emission(name, color, strength=1):
    mat, nodes, links = material(name)
    shader = nodes.new('ShaderNodeEmission')
    shader.inputs['Color'].default_value = (*color, 1)
    shader.inputs['Strength'].default_value = strength
    links.new(shader.outputs[0], nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    return mat


def plane(name, width, height, y, z):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(-width/2,y,z-height/2),(width/2,y,z-height/2),
                      (width/2,y,z+height/2),(-width/2,y,z+height/2)], [], [(0,1,2,3)])
    mesh.uv_layers.new()
    for loop, uv in zip(mesh.uv_layers.active.data, [(0,0),(1,0),(1,1),(0,1)]): loop.uv = uv
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def image_node(nodes, path):
    node = nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(str(path), check_existing=True)
    node.interpolation = 'Linear'
    node.extension = 'CLIP'
    return node


def character(layers):
    obj = plane('Fina illustration (stationary)', 4.803, 7.2, 0, 5.65)
    mat, nodes, links = material('Fina — closed eyes to red eyes')
    uv = nodes.new('ShaderNodeTexCoord')
    closed = image_node(nodes, layers/'fina_closed.png')
    opened = image_node(nodes, layers/'fina_open.png')
    links.new(uv.outputs['UV'], closed.inputs['Vector'])
    # The generated eye plate is registered locally, never crossfade the hair,
    # hands or silhouette. Sampling a small UV offset aligns the two eye lines.
    offset = nodes.new('ShaderNodeVectorMath'); offset.operation = 'ADD'
    offset.inputs[1].default_value = (.004, .006, 0)
    links.new(uv.outputs['UV'], offset.inputs[0]); links.new(offset.outputs[0], opened.inputs['Vector'])
    center = nodes.new('ShaderNodeVectorMath'); center.operation = 'SUBTRACT'
    center.inputs[1].default_value = (.503, .881, 0)
    links.new(uv.outputs['UV'], center.inputs[0])
    scale = nodes.new('ShaderNodeVectorMath'); scale.operation = 'MULTIPLY'
    scale.inputs[1].default_value = (1/.078, 1/.017, 0)
    links.new(center.outputs[0], scale.inputs[0])
    distance = nodes.new('ShaderNodeVectorMath'); distance.operation = 'LENGTH'
    links.new(scale.outputs[0], distance.inputs[0])
    mask = nodes.new('ShaderNodeMapRange'); mask.clamp = True
    mask.inputs['From Min'].default_value = .72; mask.inputs['From Max'].default_value = 1
    mask.inputs['To Min'].default_value = 1; mask.inputs['To Max'].default_value = 0
    links.new(distance.outputs['Value'], mask.inputs['Value'])
    opening = nodes.new('ShaderNodeValue'); opening.name = 'Eye opening'
    for frame, value in [(1,0),(156,0),(177,1),(192,1)]:
        opening.outputs[0].default_value = value
        opening.outputs[0].keyframe_insert('default_value',frame=frame)
    amount = nodes.new('ShaderNodeMath'); amount.operation = 'MULTIPLY'
    links.new(mask.outputs['Result'], amount.inputs[0]); links.new(opening.outputs[0], amount.inputs[1])
    color = nodes.new('ShaderNodeMixRGB'); color.blend_type = 'MIX'
    links.new(amount.outputs[0], color.inputs[0]); links.new(closed.outputs['Color'],color.inputs[1]); links.new(opened.outputs['Color'],color.inputs[2])
    light = nodes.new('ShaderNodeEmission'); light.inputs['Strength'].default_value = 1
    links.new(color.outputs[0], light.inputs['Color'])
    alpha = nodes.new('ShaderNodeMixShader')
    links.new(closed.outputs['Alpha'], alpha.inputs[0])
    links.new(nodes.new('ShaderNodeBsdfTransparent').outputs[0], alpha.inputs[1]); links.new(light.outputs[0],alpha.inputs[2])
    links.new(alpha.outputs[0], nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    obj.data.materials.append(mat)
    return obj


def crystal():
    sides = 8
    rings = [(0.5,0), (3.1,1.8), (6.7,2.95), (8.2,1.8), (10.6,0)]
    vertices = [(r*math.cos(2*math.pi*i/sides),r*math.sin(2*math.pi*i/sides),z)
                for z,r in rings for i in range(sides)]
    faces = []
    for ring in range(len(rings)-1):
        for i in range(sides):
            a=ring*sides+i; b=ring*sides+(i+1)%sides; c=(ring+1)*sides+(i+1)%sides; d=(ring+1)*sides+i
            faces.append((a,b,c,d))
    mesh = bpy.data.meshes.new('Intact faceted crystal')
    mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new('Crystal — continuous vertical spin',mesh);bpy.context.collection.objects.link(obj)
    palette=[(.72,.9,1),(.68,.82,1),(.8,.78,1),(.72,.96,1)]
    for i,color in enumerate(palette):
        mat,nodes,links=material('Clear crystal facet '+str(i))
        clear=nodes.new('ShaderNodeBsdfTransparent')
        # Deterministic clear-glass illustration shading. Avoid noisy stochastic
        # transmission over a luminous photographic layer at preview sample counts.
        clear.inputs['Color'].default_value=(.91,.955,1,1)
        reflection=nodes.new('ShaderNodeTexEnvironment')
        reflection.image=bpy.data.images.load(str(ROOT/'artwork/crystal_fina_layers/sanctuary.png'),check_existing=True)
        coord=nodes.new('ShaderNodeTexCoord');links.new(coord.outputs['Reflection'],reflection.inputs['Vector'])
        tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
        links.new(reflection.outputs[0],tint.inputs[1]);tint.inputs[2].default_value=(*color,1)
        fresnel=nodes.new('ShaderNodeFresnel');fresnel.inputs['IOR'].default_value=1.35
        strength=nodes.new('ShaderNodeMath');strength.operation='MULTIPLY_ADD'
        links.new(fresnel.outputs[0],strength.inputs[0]);strength.inputs[1].default_value=1.1;strength.inputs[2].default_value=.065
        reflected=nodes.new('ShaderNodeEmission');links.new(tint.outputs[0],reflected.inputs['Color']);links.new(strength.outputs[0],reflected.inputs['Strength'])
        mix=nodes.new('ShaderNodeAddShader')
        links.new(clear.outputs[0],mix.inputs[0]);links.new(reflected.outputs[0],mix.inputs[1])
        links.new(mix.outputs[0],nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
        obj.data.materials.append(mat)
    for face in mesh.polygons:face.material_index=(face.index//sides+face.index)%len(palette)
    edges=bpy.data.curves.new('Unbroken facet edges','CURVE');edges.dimensions='3D'
    edges.bevel_depth=.0035;edges.bevel_resolution=1;edges.resolution_u=1
    unique=set()
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):
            p,q=vertices[a],vertices[b]
            if p==q:continue
            unique.add(tuple(sorted((p,q))))
    for p,q in sorted(unique):
        line=edges.splines.new('POLY');line.points.add(1)
        line.points[0].co=(*p,1);line.points[1].co=(*q,1)
    # The changing facet reflections define the intact edges. Do not draw a
    # wire cage across Fina's face or add fracture-like overlay lines.
    return obj


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--frames',default='all')
    parser.add_argument('--width',type=int,default=1280)
    parser.add_argument('--samples',type=int,default=4)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=args.samples;scene.cycles.use_denoising=False
    scene.cycles.max_bounces=5;scene.cycles.transparent_max_bounces=16
    scene.cycles.diffuse_bounces=0;scene.cycles.glossy_bounces=2;scene.cycles.transmission_bounces=3
    scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width*9/16)
    scene.render.resolution_percentage=100;scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=FRAMES
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=35
    layers=ROOT/'artwork/crystal_fina_layers'
    world=bpy.data.worlds.new('Blue sanctuary reflections');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.12,.22,.4,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    background=plane('Sanctuary background',70,39.375,19,8.3)
    mat,nodes,links=material('Sanctuary image')
    texture=image_node(nodes,layers/'sanctuary.png');light=nodes.new('ShaderNodeEmission')
    links.new(texture.outputs['Color'],light.inputs['Color']);links.new(light.outputs[0],nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    background.data.materials.append(mat)
    character(layers);shell=crystal()
    for name,position,power,size,color in [('Left softbox',(-5,-7,9),900,5,(.66,.8,1)),
                                         ('Right softbox',(6,-3,7),1100,4,(.85,.83,1)),
                                         ('Top glint',(-1,2,14),1400,3,(.65,.82,1))]:
        lamp=bpy.data.lights.new(name,'AREA');lamp.energy=power;lamp.shape='DISK';lamp.size=size;lamp.color=color
        obj=bpy.data.objects.new(name,lamp);bpy.context.collection.objects.link(obj);obj.location=position
        obj.rotation_euler=(Vector((0,0,5.6))-obj.location).to_track_quat('-Z','Y').to_euler()
    rng=random.Random(13503);motes=[]
    dot=emission('Floating light',(.58,.78,1),1.8)
    for i in range(48):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=rng.uniform(.007,.018))
        obj=bpy.context.object;obj.name='Mote '+str(i);obj.data.materials.append(dot)
        motes.append((obj,rng.uniform(-2.7,2.7),rng.uniform(-1.5,1.5),rng.uniform(1,10),rng.uniform(.035,.09),rng.uniform(0,6)))
    camera_data=bpy.data.cameras.new('Wide to awakening');camera_data.lens=30;camera_data.sensor_width=36
    camera=bpy.data.objects.new('Wide to awakening',camera_data);bpy.context.collection.objects.link(camera);scene.camera=camera
    def pose(frame):
        t=(frame-1)/FPS;progress=t/((FRAMES-1)/FPS)
        zoom=1+4.05*progress
        # Raise the framing before the narrowing view could crop her head.
        focus=5.55+2.75*(1-(1-progress)**2)
        camera.location=(0,-19/zoom,focus+.8*(1-progress))
        camera.rotation_euler=(Vector((0,0,focus))-camera.location).to_track_quat('-Z','Y').to_euler()
        shell.rotation_euler.z=math.radians(10+15*t)
        for obj,x,y,z,speed,phase in motes:
            obj.location=(x+.025*math.sin(t+phase),y,1+(z-1+t*speed)%9)
    # Save a complete scene with sampled camera/spin animation for review.
    for frame in range(1,FRAMES+1):
        pose(frame)
        camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_euler',frame=frame)
        shell.keyframe_insert('rotation_euler',frame=frame)
    for obj in (camera,shell):
        for curve in obj.animation_data.action.fcurves:
            for key in curve.keyframe_points:key.interpolation='LINEAR'
    scene.frame_set(1);pose(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'Crystal-Fina-Intact.blend'))
    frames=range(1,FRAMES+1) if args.frames=='all' else [int(x) for x in args.frames.split(',')]
    for frame in frames:
        scene.frame_set(frame);pose(frame);scene.render.filepath=str(args.output/f'frame-{frame:04d}.png')
        bpy.ops.render.render(write_still=True)
    report={'schema':1,'revision':'crystal-fina-film-2','fps':FPS,'frames':FRAMES,'seconds':FRAMES/FPS,
            'width':args.width,'height':round(args.width*9/16),'method':'Illustrated Fina; rotating 3D crystal; wide-to-close camera; red eyes opening',
            'spinDegreesPerSecond':15,'spinAxis':'vertical','cameraZoom':[1,5.05],
            'eyesOpenFrames':[156,177],'fractures':False,'shards':False,'whiteout':False,
            'layers':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(layers.glob('*.png'))}}
    (args.output/'scene.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
