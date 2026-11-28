// W128: read-only OCR box locator. Prints every exact-text match with its screen centre.
// Usage: morwen_label_boxes SCREENSHOT.png REGEX  -> JSON {screenshot_sha256, matches:[{label,x,y}]}
import Foundation
import Vision
import CryptoKit

let a = CommandLine.arguments
guard a.count == 3 else { FileHandle.standardError.write(Data("usage\n".utf8)); exit(2) }
let url = URL(fileURLWithPath: a[1])
let data = try Data(contentsOf: url)
let hash = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
let r = VNRecognizeTextRequest()
r.recognitionLevel = .accurate
try VNImageRequestHandler(url: url).perform([r])
var out: [[String: Any]] = []
for o in r.results ?? [] {
    guard let t = o.topCandidates(1).first?.string.trimmingCharacters(in: .whitespacesAndNewlines) else { continue }
    guard t.range(of: a[2], options: .regularExpression) != nil else { continue }
    out.append(["label": t, "x": o.boundingBox.midX * 1024, "y": (1 - o.boundingBox.midY) * 768,
                "w": o.boundingBox.width * 1024, "h": o.boundingBox.height * 768])
}
out.sort { ($0["y"] as! Double) < ($1["y"] as! Double) }
let json = try JSONSerialization.data(withJSONObject: ["screen_px": [1024, 768], "screenshot_sha256": hash, "matches": out], options: [.sortedKeys])
FileHandle.standardOutput.write(json)
