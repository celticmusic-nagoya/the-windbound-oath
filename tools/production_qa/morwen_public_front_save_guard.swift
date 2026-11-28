import Cocoa
import Foundation
import Vision
let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let im = NSBitmapImageRep(data: try Data(contentsOf: url)),
      im.pixelsWide == 1024, im.pixelsHigh == 768 else { exit(2) }
let req = VNRecognizeTextRequest()
try VNImageRequestHandler(url: url).perform([req])
func norm(_ s: String) -> String {
    // W99 diag: checked-state OCR read "• Back |"; keep letters only.
    String(String.UnicodeScalarView(s.unicodeScalars.filter { CharacterSet.letters.contains($0) }))
}
// Diagnostics (stderr) for every Front/Back observation, so a locator miss is explainable.
for o in req.results ?? [] {
    let t = o.topCandidates(1).first?.string ?? ""
    if t.contains("Front") || t.contains("Back") {
        FileHandle.standardError.write("OBS \(t) minX=\(Double(o.boundingBox.minX)*1024.0) midY=\((1.0-Double(o.boundingBox.midY))*768.0)\n".data(using:.utf8)!)
    }
}
for (label, y) in [("Front",364),("Back",399)] {
    let hits = (req.results ?? []).filter { o in
        let t = norm(o.topCandidates(1).first?.string ?? "")
        return t.hasSuffix(label) && t.count <= label.count + 1 &&
            abs((1.0-Double(o.boundingBox.midY))*768.0-Double(y)) < 9.0 &&
            Double(o.boundingBox.minX)*1024.0 > 300.0 && Double(o.boundingBox.minX)*1024.0 < 400.0
    }
    guard hits.count == 1 else { FileHandle.standardError.write("LABEL_NOT_UNIQUE \(label) \(hits.count)\n".data(using:.utf8)!); exit(2) }
}
func state(_ y: Int) -> String {
    var blue = 0, white = 0
    for yy in (y-5)...(y+5) {
        for x in 343...353 {
            guard let c = im.colorAt(x:x,y:yy)?.usingColorSpace(.deviceRGB) else { return "unknown" }
            if c.blueComponent>0.72 && c.redComponent<0.30 && c.greenComponent>0.24 && c.greenComponent<0.85 { blue += 1 }
            if c.redComponent>0.9 && c.greenComponent>0.9 && c.blueComponent>0.9 { white += 1 }
        }
    }
    if blue>=20 { return "checked" }
    if white>=100 && blue==0 { return "unchecked" }
    return "unknown"
}
let front=state(364), back=state(399)
print("Front",front,"Back",back)
exit(front=="checked" && back=="unchecked" ? 0 : 1)
