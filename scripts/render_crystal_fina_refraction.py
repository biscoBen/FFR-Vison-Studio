"""Original independent 3D spin and eye-only awakening; vary the outer optical material."""
from pathlib import Path
import argparse,sys,json,hashlib
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import render_crystal_fina_rotation as base
p=argparse.ArgumentParser(add_help=False);p.add_argument('--variant',choices=['lighter','denser'],required=True)
a,rest=p.parse_known_args(sys.argv[sys.argv.index('--')+1:]);variant=a.variant
sys.argv=sys.argv[:sys.argv.index('--')+1]+rest
original=base.crystal
TEXTURE=ROOT/'artwork/crystal_fina_optics/refraction.png'

def mathnode(n,l,op,a,b):
 node=n.new('ShaderNodeMath');node.operation=op
 for i,value in enumerate((a,b)):
  if isinstance(value,(float,int)):node.inputs[i].default_value=value
  else:l.new(value,node.inputs[i])
 return node.outputs[0]

def smooth(n,l,value,lo,hi):
 node=n.new('ShaderNodeMapRange');node.clamp=True;node.interpolation_type='SMOOTHSTEP';node.inputs['From Min'].default_value=lo;node.inputs['From Max'].default_value=hi;l.new(value,node.inputs['Value']);return node.outputs['Result']

def crystal():
 obj=original()
 for i,mat in enumerate(obj.data.materials):
  n=mat.node_tree.nodes;l=mat.node_tree.links
  output=next(x for x in n if x.bl_idname=='ShaderNodeOutputMaterial')
  previous=output.inputs['Surface'].links[0].from_socket
  clear=next(x for x in n if x.bl_idname=='ShaderNodeBsdfTransparent')
  coord=n.new('ShaderNodeTexCoord');xyz=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['Generated'],xyz.inputs[0])
  top=mathnode(n,l,'SUBTRACT',1,smooth(n,l,xyz.outputs['Z'],.67,.80));bottom=smooth(n,l,xyz.outputs['Z'],.08,.30)
  band=mathnode(n,l,'MULTIPLY',top,bottom)
  plane=n.new('ShaderNodeCombineXYZ');l.new(xyz.outputs['X'],plane.inputs['X']);l.new(xyz.outputs['Z'],plane.inputs['Y'])
  optical=base.image_node(n,TEXTURE);optical.extension='REPEAT';l.new(plane.outputs[0],optical.inputs['Vector'])
  luma=n.new('ShaderNodeRGBToBW');l.new(optical.outputs['Color'],luma.inputs[0])
  amplitude=n.new('ShaderNodeValue');amplitude.name='Outer crystal optical density';amplitude.outputs[0].default_value=.50 if variant=='lighter' else .75
  density=mathnode(n,l,'ADD',mathnode(n,l,'MULTIPLY',luma.outputs[0],amplitude.outputs[0]),.18 if variant=='lighter' else .25)
  opacity=mathnode(n,l,'MULTIPLY',band,density)
  transmission=mathnode(n,l,'SUBTRACT',1,opacity)
  tint=n.new('ShaderNodeVectorMath');tint.operation='SCALE';tint.inputs[0].default_value=(.91,.955,1);l.new(transmission,tint.inputs['Scale']);l.new(tint.outputs[0],clear.inputs['Color'])
  color=n.new('ShaderNodeMixRGB');color.inputs[0].default_value=.3;color.inputs[2].default_value=(.68,.84,1,1);l.new(optical.outputs['Color'],color.inputs[1])
  frost=n.new('ShaderNodeEmission');l.new(color.outputs[0],frost.inputs['Color']);l.new(mathnode(n,l,'MULTIPLY',opacity,1.5),frost.inputs['Strength'])
  combined=n.new('ShaderNodeAddShader');l.new(previous,combined.inputs[0]);l.new(frost.outputs[0],combined.inputs[1]);l.new(combined.outputs[0],output.inputs['Surface'])
 return obj
original_character=base.character
def character(layers):
 obj=original_character(layers)
 mat=obj.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links
 closed=next(x for x in n if x.bl_idname=='ShaderNodeTexImage' and x.image.filepath.endswith('fina_closed.png'))
 uv=next(x for x in n if x.bl_idname=='ShaderNodeTexCoord')
 xyz=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],xyz.inputs[0])
 low=smooth(n,l,xyz.outputs['Y'],.21,.35);high=mathnode(n,l,'SUBTRACT',1,smooth(n,l,xyz.outputs['Y'],.69,.80))
 band=mathnode(n,l,'MULTIPLY',low,high)
 channels=n.new('ShaderNodeSeparateColor');channels.mode='RGB';l.new(closed.outputs['Color'],channels.inputs['Color'])
 blue=mathnode(n,l,'SUBTRACT',channels.outputs['Blue'],channels.outputs['Red'])
 optical=smooth(n,l,blue,-.01,.08)
 thinner=mathnode(n,l,'SUBTRACT',1,mathnode(n,l,'MULTIPLY',mathnode(n,l,'MULTIPLY',band,optical),.65))
 alpha=next(x for x in n if x.bl_idname=='ShaderNodeMixShader')
 l.new(mathnode(n,l,'MULTIPLY',closed.outputs['Alpha'],thinner),alpha.inputs[0])
 return obj
base.character=character
base.crystal=crystal
base.main()
out=Path(rest[rest.index('--output')+1]);m=json.loads((out/'scene.json').read_text());m.update(materialVariant=variant,characterSourceUnchanged=True,geometry='Original full 3D octagonal crystal mesh',onlyEyeRegionChanges=True,fullFaceDissolve=False,internalCrystalHighlights='Static blue-highlight transmission; face and source images unchanged',opticalTexture=str(TEXTURE),opticalTextureSha256=hashlib.sha256(TEXTURE.read_bytes()).hexdigest(),method='Original independent 15-degree/second 3D crystal rotation and camera; stationary illustration; original eye-region-only awakening; outer facet optical-density variants')
(out/'scene.json').write_text(json.dumps(m,indent=2)+'\n')
