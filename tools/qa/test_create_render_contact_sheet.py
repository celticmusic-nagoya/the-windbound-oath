import json,pathlib,tempfile,unittest,sys
from PIL import Image
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from create_render_contact_sheet import build
class PreviewTests(unittest.TestCase):
 def test_manifest_and_preview(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/"renders";out=src/"previews";src.mkdir()
   Image.new("RGBA",(16,24),(90,40,100,255)).save(src/"FRONT.png")
   build(src,out)
   self.assertTrue((out/"RENDER_PREVIEW_CONTACT_SHEET.png").is_file())
   report=json.loads((out/"RENDER_PREVIEW_MANIFEST.json").read_text())
   self.assertEqual(report["shown"],1)
   self.assertEqual(report["images"][0]["path"],"FRONT.png")
   self.assertFalse(report["production_approval"])
   build(src,out)
   self.assertEqual(json.loads((out/"RENDER_PREVIEW_MANIFEST.json").read_text())["source_images_total"],1)
 def test_empty_is_blocked(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   with self.assertRaises(SystemExit):build(root,root/"previews")
if __name__=="__main__":unittest.main()
