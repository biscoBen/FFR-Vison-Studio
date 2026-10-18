"""Every mesh keeps its authored origin when a bitmap is centred for playback."""
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'assets/existing_visions/payload'))
import _ffr_ffbe_renderer as r


class MeshProjectionTests(unittest.TestCase):
    def test_projected_points_match_after_bitmap_scale_rotation_and_mirror(self):
        mesh={'vertices':[(4,-3,-2),(10,5,4),(7,2,1)]}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'offset.m3r').write_bytes(b'explicit mocked model')
            with patch.object(r,'parse_m3r',return_value=mesh):
                for tilt in ((0,0),(20,0),(-25,35)):
                    projection=r.model_projection('offset',[tmp],*tilt)
                    points=r.project_mesh_vertices(mesh,*tilt)
                    for scale in ((2,3),(-2,.5)):
                        size=[2*projection[1][a]*scale[a] for a in (0,1)]
                        for angle in (0,90,-37):
                            for mirror in (False,True):
                                origin=[15,-9,7]
                                pos=r.mesh_position(origin,size,projection,angle,mirror)
                                ca,sa=math.cos(math.radians(angle)),math.sin(math.radians(angle))
                                for p in points:
                                    local=[(p[a]-projection[0][a])*scale[a] for a in (0,1)]
                                    local[0]*=-1 if mirror else 1
                                    drawn=[pos[0]+ca*local[0]-sa*local[1],pos[1]+sa*local[0]+ca*local[1]]
                                    actual=[p[0]*scale[0]*(-1 if mirror else 1),p[1]*scale[1]]
                                    expected=[origin[0]+ca*actual[0]-sa*actual[1],origin[1]+sa*actual[0]+ca*actual[1]]
                                    for a in (0,1):self.assertAlmostEqual(drawn[a],expected[a])
                                self.assertEqual(pos[2],7)

    def test_centred_mesh_is_unchanged_and_cache_is_scoped_to_asset_directory(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            for folder in (a,b):(Path(folder)/'same.m3r').touch()
            with patch.object(r,'parse_m3r',side_effect=[{'vertices':[(-1,-2,0),(1,2,0)]},
                                                        {'vertices':[(4,8,0),(6,12,0)]}]):
                first=r.model_projection('same',[a]);second=r.model_projection('same',[b])
                self.assertEqual(first,((0,0),(1,2)))
                self.assertEqual(second,((5,10),(1,2)))
                self.assertEqual(r.mesh_position([3,7,2],[10,20],first,35,True),[3,7,2])

if __name__=='__main__':unittest.main()
