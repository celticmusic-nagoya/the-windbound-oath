import sys,json,unittest,pathlib,hashlib
sys.path.insert(0,'tools/character-asset-studio/pipeline/tests')
import test_pipeline as t
from PIL import Image, __version__ as pillow_version
import numpy as np
rows=[]
class Result(unittest.TextTestResult):
 def addFailure(self,test,err):
  super().addFailure(test,err)
  cls=test.__class__.__name__
  if cls=='V07Layer0':a,b,suffix=test.tmp/'o',test.COMMITTED,'body_guide'
  elif cls=='V07Normalize':a,b,suffix=test.tmp/'a',t.STUDIO/'normalized/morwen-final-canon-20261111',None
  elif cls=='V08MasterBody':a,b,suffix=test.tmp,test.O,'structure_guide'
  else:return
  for v in t.core.VIEWS:
   name=f'{v}_{suffix}.png' if suffix else f'{v}.png'
   x,y=a/name,b/name
   with Image.open(x) as ix, Image.open(y) as iy:
    ax,ay=np.asarray(ix.convert('RGBA')),np.asarray(iy.convert('RGBA'))
    same=ax.shape==ay.shape and np.array_equal(ax,ay)
    rows.append({'testId':test.id(),'view':v,'sameDecodedRGBA':bool(same),'differentPixels':int(np.any(ax!=ay,axis=2).sum()) if ax.shape==ay.shape else None,'generatedSha256':hashlib.sha256(x.read_bytes()).hexdigest(),'archivedSha256':hashlib.sha256(y.read_bytes()).hexdigest(),'generatedInfo':str(ix.info),'archivedInfo':str(iy.info)})
suite=unittest.defaultTestLoader.loadTestsFromModule(t)
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
pathlib.Path(__file__).with_name('PIPELINE_PIXEL_DIAGNOSTIC_REPLAY.json').write_text(json.dumps({'pillowVersion':pillow_version,'comparisons':rows},indent=2))
raise SystemExit(not r.wasSuccessful())
