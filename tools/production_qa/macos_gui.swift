// macOS GUI primitives for isolated production runners. Normalized display coordinates.
import Foundation
import CoreGraphics
import Vision

func fail(_ message: String) -> Never { FileHandle.standardError.write(Data((message+"\n").utf8)); exit(2) }
let a = Array(CommandLine.arguments.dropFirst())
guard let op = a.first else { fail("missing operation") }
let d = CGDisplayBounds(CGMainDisplayID())
guard let s = CGEventSource(stateID: .combinedSessionState) else { fail("event source unavailable") }
func number(_ i: Int, _ lo: Double, _ hi: Double) -> Double {
    guard i < a.count, let n = Double(a[i]), n.isFinite, n >= lo, n <= hi else { fail("invalid argument") }
    return n
}
func point(_ i: Int) -> CGPoint { CGPoint(x: d.minX + number(i,0,1)*d.width, y: d.minY + number(i+1,0,1)*d.height) }
func mouse(_ type: CGEventType, _ p: CGPoint, _ button: CGMouseButton = .left, _ count: Int64 = 1) {
    guard let e = CGEvent(mouseEventSource:s,mouseType:type,mouseCursorPosition:p,mouseButton:button) else { fail("mouse event unavailable") }
    e.setIntegerValueField(.mouseEventClickState,value:count)
    e.post(tap:.cgSessionEventTap)
}
func click(_ p: CGPoint,_ right: Bool=false,_ count: Int=1) {
    mouse(.mouseMoved,p); usleep(150000)
    for i in 1...count {
        mouse(right ? .rightMouseDown : .leftMouseDown,p,right ? .right : .left,Int64(i))
        usleep(60000)
        mouse(right ? .rightMouseUp : .leftMouseUp,p,right ? .right : .left,Int64(i))
        usleep(90000)
    }
}
func key(_ k: CGKeyCode,_ flags: CGEventFlags) {
    for down in [true,false] {
        guard let e = CGEvent(keyboardEventSource:s,virtualKey:k,keyDown:down) else { fail("keyboard event unavailable") }
        e.flags=flags; e.post(tap:.cgSessionEventTap); usleep(60000)
    }
}
switch op {
case "move": mouse(.mouseMoved,point(1))
case "click","right-click","double-click": click(point(1),op=="right-click",op=="double-click" ? 2 : 1)
case "drag","slider","rotate":
    let p=point(1), q=point(3), seconds=number(5,0.2,10)
    let steps=Int(seconds*60)
    mouse(.mouseMoved,p); mouse(.leftMouseDown,p)
    for i in 1...steps {
        let t=CGFloat(i)/CGFloat(steps)
        mouse(.leftMouseDragged,CGPoint(x:p.x+(q.x-p.x)*t,y:p.y+(q.y-p.y)*t))
        usleep(16667)
    }
    mouse(.leftMouseUp,q)
case "scroll","zoom":
    let p=point(1), vertical=Int32(number(3,-100,100)), horizontal=Int32(number(4,-100,100))
    mouse(.mouseMoved,p)
    guard let e=CGEvent(scrollWheelEvent2Source:s,units:.line,wheelCount:2,wheel1:vertical,wheel2:horizontal,wheel3:0) else { fail("scroll unavailable") }
    e.post(tap:.cgSessionEventTap)
case "key":
    let k=CGKeyCode(number(1,0,127))
    var flags=CGEventFlags()
    for flag in a.dropFirst(2) {
        switch flag { case "cmd": flags.insert(.maskCommand); case "shift": flags.insert(.maskShift); case "ctrl": flags.insert(.maskControl); case "alt": flags.insert(.maskAlternate); default: fail("unknown modifier") }
    }
    key(k,flags)
case "text":
    guard a.count==2,a[1].utf16.count<=4096 else { fail("invalid text") }
    let u=Array(a[1].utf16)
    for down in [true,false] {
        guard let e=CGEvent(keyboardEventSource:s,virtualKey:0,keyDown:down) else { fail("text event unavailable") }
        u.withUnsafeBufferPointer { e.keyboardSetUnicodeString(stringLength:u.count,unicodeString:$0.baseAddress) }
        e.post(tap:.cgSessionEventTap)
    }
case "ocr","click-label":
    guard a.count >= 2 else { fail("missing screenshot") }
    let r=VNRecognizeTextRequest()
    try VNImageRequestHandler(url:URL(fileURLWithPath:a[1])).perform([r])
    let observations=r.results ?? []
    let labels=observations.compactMap{$0.topCandidates(1).first?.string}
    print(labels.joined(separator:" | "))
    if op=="click-label" {
        guard a.count==4,labels.contains(where:{$0.contains(a[3])}) else { fail("screen anchor missing") }
        // Vision may group adjacent controls in one observation. Locate exact word ranges.
        var boxes: [CGRect] = []
        for observation in observations {
            guard let candidate = observation.topCandidates(1).first else { continue }
            let t = candidate.string
            if t.trimmingCharacters(in: .whitespacesAndNewlines) == a[2] {
                boxes.append(observation.boundingBox)
                continue
            }
            // Only allow known combined home controls, never arbitrary substring clicks.
            let normalized = t.replacingOccurrences(of:"•",with:" ").split(whereSeparator:{$0.isWhitespace}).joined(separator:" ")
            guard a[2]=="Open", a[3]=="Recently Edited", ["New Open","Open"].contains(normalized),
                  let range=t.range(of:"Open"), let box=try candidate.boundingBox(for:range) else { continue }
            boxes.append(box.boundingBox)
        }
        guard boxes.count==1,let box=boxes.first else { fail("label not unique") }
        click(CGPoint(x:d.minX+box.midX*d.width,y:d.minY+(1-box.midY)*d.height))
    }
case "screenshot":
    guard a.count==2,a[1].hasSuffix(".png") else { fail("invalid output") }
    let p=Process(); p.executableURL=URL(fileURLWithPath:"/usr/sbin/screencapture"); p.arguments=["-x",a[1]]; try p.run(); p.waitUntilExit()
    guard p.terminationStatus==0 else { fail("capture failed") }
default: fail("unknown operation")
}
