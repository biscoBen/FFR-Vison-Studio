"""Private copy of the pinned converter's texture sampler for library previews."""
from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
import _ffr_ffbe_renderer as ibmb
import _ffr_ffbe_uv as uv_sampling
MESH_SPRITE_DIR = None

def atomic_png(image, path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.part');image.save(temporary,format='PNG');temporary.replace(path)

class TextureCache:
    def __init__(self, asset_dirs, *, virtual_cache_limit=32, virtual_cache_bytes=128 * 1024 * 1024):
        self.dirs = asset_dirs
        self.index = {}
        for d in asset_dirs:
            if not os.path.isdir(d):
                continue
            for fn in os.listdir(d):
                stem, ext = os.path.splitext(fn)
                if ext.lower() in (".png", ".tga", ".jpg"):
                    self.index.setdefault(stem.lower(), os.path.join(d, fn))
        self.cache = {}
        self.virtual_cache = OrderedDict()
        self.virtual_cache_limit = max(0, virtual_cache_limit)
        self.virtual_cache_bytes = max(0, virtual_cache_bytes)
        self.virtual_bytes = 0
        self.missing = set()

    def _store_virtual(self, name, arr):
        """Bound generated frame pixels while keeping source textures and paths."""
        key = name.lower()
        arr = np.asarray(arr, dtype=np.float32) if arr is not None else None
        self.virtual_bytes -= self.virtual_cache.pop(key, 0)
        self.cache[key] = arr
        size = arr.nbytes if arr is not None else 0
        self.virtual_cache[key] = size
        self.virtual_bytes += size
        while len(self.virtual_cache) > self.virtual_cache_limit or self.virtual_bytes > self.virtual_cache_bytes:
            oldest, size = self.virtual_cache.popitem(last=False)
            self.virtual_bytes -= size
            self.cache.pop(oldest, None)
        return arr

    def get(self, name):
        """Return an HxWx4 float32 array in 0..1 (straight alpha), or None."""
        key = name.lower()
        if key in self.cache:
            if key in self.virtual_cache:
                self.virtual_cache.move_to_end(key)
            return self.cache[key]
        if name == "solid:white":
            # Native untextured particles shade vertex RGBA directly. A white
            # cell is the neutral carrier for those independently baked
            # color/alpha channels in SpriteStudio; it is not replacement art.
            path = os.path.join(MESH_SPRITE_DIR, "native_solid_white.png")
            os.makedirs(MESH_SPRITE_DIR, exist_ok=True)
            valid = False
            try:
                with Image.open(path) as cell:
                    valid = cell.mode == 'RGBA' and cell.size == (2, 2) and bool(np.all(np.asarray(cell) == 255))
            except (OSError, ValueError):
                pass
            if not valid:
                atomic_png(Image.new("RGBA", (2, 2), (255, 255, 255, 255)), path)
            self.index[key] = path
            arr = np.ones((2, 2, 4), dtype=np.float32)
            self.cache[key] = arr
            return arr
        if name.startswith("mesh:"):
            return self._mesh_sprite(name)
        if name.startswith("quadcolor:"):
            return self._quad_color_sprite(name)
        if name.startswith("nativeuv:"):
            return self._native_uv_sprite(name)
        path = self.index.get(key)
        if path is None:
            self.missing.add(name)
            self.cache[key] = None
            return None
        im = Image.open(path)
        # palette PNGs (mode "P") carry their alpha in the palette
        im = im.convert("RGBA")
        arr = np.asarray(im).astype(np.float32) / 255.0
        self.cache[key] = arr
        return arr

    def _native_uv_sprite(self, name):
        """Sample authored UV controls before geometry/vertex colour shading."""
        data = json.loads(name[len('nativeuv:'):])
        material = data.get('material')
        # Model-only emitters have no primary texture. The historical resource
        # accessor falls back to the model name, which is not a missing PNG.
        # Use the same neutral texture as the existing vertex-coloured mesh
        # rasterizer; a genuinely named but missing texture still fails.
        untextured_model = bool(data.get('model') and material and material.get('primary') is None
                                and material.get('mode') == 0 and data['texture'] == data['model'])
        texture = self.get('solid:white' if untextured_model else data['texture'])
        if texture is None:
            return self._store_virtual(name, None)
        stamp = hashlib.sha256((str(ibmb.BAKE_VERSION) + name).encode())
        stamp.update(texture.tobytes())
        secondary = None
        if material and material['mode']:
            secondary = self.get(material['secondary'])
            if secondary is None:
                raise ValueError('Missing active secondary texture '+str(material['secondary']))
            stamp.update(secondary.tobytes())
        mesh_path = None
        if data.get('model'):
            mesh_path = next((os.path.join(d, data['model']+'.m3r') for d in self.dirs
                              if os.path.isfile(os.path.join(d, data['model']+'.m3r'))), None)
            if mesh_path:
                with open(mesh_path, 'rb') as stream: stamp.update(stream.read())
        path = os.path.join(MESH_SPRITE_DIR, 'nativeuv__'+stamp.hexdigest()[:24]+'.png')
        if os.path.isfile(path):
            arr = np.asarray(Image.open(path).convert('RGBA'), dtype=np.float32)/255.
        else:
            def sampler(u, v, color=1.):
                color = color * np.asarray([*data.get('color', [1., 1., 1.]), 1.], dtype=np.float32)
                if data.get('vertexColors'):
                    tl, bl, br, tr = np.asarray(data['vertexColors'], dtype=np.float32)
                    cu, cv = np.asarray(u)[...,None], np.asarray(v)[...,None]
                    rgb = np.where(cv >= cu, tl*(1-cv)+bl*(cv-cu)+br*cu,
                                   tl*(1-cu)+br*cv+tr*(cu-cv))
                    vertex = np.concatenate([rgb, np.ones_like(cu)], axis=-1)
                    color = color * vertex
                if material:
                    return uv_sampling.shade(texture, secondary, u, v, data['channels'], material, color)
                return uv_sampling.channel_sample(texture, u, v, data['channels'][0], data['wrap']) * color
            if mesh_path:
                arr = ibmb.rasterise_mesh(ibmb.parse_m3r(mesh_path), texture,
                                         *data['tilt'], texture_sampler=sampler,
                                         fog_edge_fade=data.get('fogEdgeFade',0.))
            else:
                height, width = texture.shape[:2]
                factor = min(1., 512/max(width, height))
                width, height = max(1, round(width*factor)), max(1, round(height*factor))
                arr = sampler(*uv_sampling.grid(width, height))
                if data.get('fogEdgeFade'):
                    arr=arr.copy()
                    arr[...,3]*=ibmb.fog_edge_mask(np.ones(arr.shape[:2],dtype=bool),data['fogEdgeFade'])
            if arr is None:
                # A fully culled/degenerate projected mesh has no covered
                # pixels. Retain a transparent cell for its virtual texture;
                # exporting the literal nativeuv JSON as a filename is invalid.
                arr = np.zeros((1, 1, 4), dtype=np.float32)
            os.makedirs(MESH_SPRITE_DIR, exist_ok=True)
            atomic_png(Image.fromarray((np.clip(arr, 0, 1)*255).astype(np.uint8), 'RGBA'), path)
        self.index[name.lower()] = path
        return self._store_virtual(name, arr)

    def _quad_color_sprite(self, name):
        """Bake native four-corner RGB into a texture; alpha stays separate."""
        source, payload = name[len("quadcolor:"):].rsplit("|", 1)
        colors, region, flips = json.loads(payload)
        texture = self.get(source)
        if texture is None:
            return None
        stamp = hashlib.sha256(name.encode())
        stamp.update(str(ibmb.BAKE_VERSION).encode())
        stamp.update(texture.tobytes())
        path = os.path.join(MESH_SPRITE_DIR, "quadcolor__" + stamp.hexdigest()[:24] + ".png")
        if os.path.exists(path):
            arr = np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255.
        else:
            # A white 2px source still needs enough texels for its authored
            # gradient; this changes sampling resolution, never world size.
            h, w = texture.shape[:2]
            h, w = max(64, h), max(64, w)
            raw = Image.fromarray((np.clip(texture, 0, 1) * 255).astype(np.uint8), "RGBA")
            arr = np.asarray(raw.resize((w, h), Image.Resampling.BILINEAR), dtype=np.float32) / 255.
            arr = arr.copy()
            u = (np.arange(w, dtype=np.float32) + .5) / w
            v = (np.arange(h, dtype=np.float32) + .5) / h
            if flips[0]: u = 1 - u
            if flips[1]: v = 1 - v
            u, v = np.meshgrid(region[0] + u * (region[2] - region[0]),
                               region[1] + v * (region[3] - region[1]))
            u, v = u[..., None], v[..., None]
            tl, bl, br, tr = np.asarray(colors, dtype=np.float32)
            tint = np.where(v >= u, tl * (1-v) + bl * (v-u) + br * u,
                            tl * (1-u) + br * v + tr * (u-v))
            arr[..., :3] *= tint
            os.makedirs(MESH_SPRITE_DIR, exist_ok=True)
            atomic_png(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA"), path)
        self.index[name.lower()] = path
        return self._store_virtual(name, arr)


    def _mesh_sprite(self, name):
        """'mesh:<model>|<texture>|<rx>|<ry>' -> the mesh rasterised with its
        texture, saved once under build/effects/textures (where to_ss6.py also
        looks) and indexed like any other texture."""
        key = name.lower()
        fields=name[5:].split('|');model,tex_name,rx,ry=fields[:4]
        fog_edge_fade=.075 if fields[4:]==['fog-edges-v1'] else 0.
        mpath = next((os.path.join(d, model + ".m3r") for d in self.dirs if os.path.exists(os.path.join(d, model + ".m3r"))), None)
        texture_path = self.index.get(tex_name.lower())
        stamp = hashlib.sha256((str(ibmb.BAKE_VERSION)+str(fog_edge_fade)).encode())
        for dependency in (mpath, texture_path):
            if dependency:
                with open(dependency, 'rb') as stream:
                    stamp.update(stream.read())
        fname = "mesh__%s__%s__x%s_y%s__%s.png" % (model, tex_name, rx, ry, stamp.hexdigest()[:12])
        fname = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in fname)
        path = os.path.join(MESH_SPRITE_DIR, fname)
        if os.path.exists(path):
            arr = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0
        else:
            arr = None
            tex = self.get(tex_name)
            if mpath:
                try:
                    arr = ibmb.rasterise_mesh(ibmb.parse_m3r(mpath), tex, float(rx), float(ry),fog_edge_fade=fog_edge_fade)
                except Exception as ex:  # pragma: no cover - diagnostics only
                    print("mesh sprite failed for %s: %s" % (name, ex), file=sys.stderr)
            if arr is None:
                if tex is not None:
                    self.index[key] = self.index.get(tex_name.lower())
                return self._store_virtual(name, tex)  # no mesh: the plain textured quad as before
            os.makedirs(MESH_SPRITE_DIR, exist_ok=True)
            atomic_png(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA"), path)
        self.index[key] = path
        return self._store_virtual(name, arr)
