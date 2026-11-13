"""Static safety and asset-path QA for mobile landmark review page."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib, subprocess, tempfile

root=Path(__file__).resolve().parents[3]
page=root/"tools/blender/morwen_production/landmark-review.html"
html=page.read_text(encoding="utf-8")
class Elements(HTMLParser):
 def __init__(self):
  super().__init__();self.ids=set();self.scripts=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if "id" in attrs:
   assert attrs["id"] not in self.ids,("duplicate id",attrs["id"])
   self.ids.add(attrs["id"])
parser=Elements();parser.feed(html)
assert {"view","point","ref","overlay","undo","export","output"}<=parser.ids
assert "MANUAL_UNREVIEWED" in html and "MORWEN-LANDMARK-REVIEW-UNAPPROVED" in html
assert "navigator.clipboard" in html and "canvas.addEventListener" in html
assert "fetch(" not in html and "localStorage" not in html and "eval(" not in html
assert html.count("<script>")==1 and html.count("</script>")==1
script=html.split("<script>",1)[1].split("</script>",1)[0]
with tempfile.TemporaryDirectory() as temp:
 js=Path(temp)/"landmark-review.js";js.write_text(script,encoding="utf-8")
 subprocess.run(["node","--check",str(js)],check=True)
references={"7809.png":"b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed",
"7807.png":"9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737",
"7810.png":"b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f",
"7808.png":"69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa"}
for name,sha in references.items():
 assert f'../production_mesh_08/references/{name}' in html
 image=(page.parent/"../production_mesh_08/references"/name).resolve()
 assert image.is_file(),image
 assert hashlib.sha256(image.read_bytes()).hexdigest()==sha
print("LANDMARK REVIEW STATIC QA PASS: JS syntax, 7 controls, 4 canonical image hashes, no remote upload")
