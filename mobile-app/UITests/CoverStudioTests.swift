import XCTest
import Vision

/// Runner installs into a newly created simulator and a unique QA App Group.
final class CoverStudioTests:XCTestCase {
    private let app=XCUIApplication(bundleIdentifier:"local.silver.shiji.v64.qa")
    override func setUpWithError() throws {continueAfterFailure=false;app.launchArguments=["-shiji-v2-motion-mode","calm"];app.launch()}
    private func capture(_ name:String){let shot=XCTAttachment(screenshot:app.screenshot());shot.name=name;shot.lifetime = .keepAlways;add(shot)}
    private func reveal(_ element:XCUIElement,in scroll:XCUIElement?=nil){
        let target=scroll?.exists==true ? scroll! : app.scrollViews.firstMatch.exists ? app.scrollViews.firstMatch : app
        for _ in 0..<12{
            if !element.exists{target.swipeUp();continue}
            let frame=element.frame,height=app.frame.height
            if element.isHittable && frame.minY>=150 && frame.maxY<height-160{return}
            if element.exists && frame.minY<150{target.swipeDown()}else{target.swipeUp()}
        }
        XCTAssertTrue(element.isHittable,"Control was not reachable: \(element)")
    }
    func testActualNativeCoverSaveCancelAndReset() throws {
        let resource=app.buttons.matching(NSPredicate(format:"label CONTAINS %@","SHIJI Cover QA")).firstMatch
        for _ in 0..<8{if resource.exists{break};app.swipeUp()};XCTAssertTrue(resource.waitForExistence(timeout:20));reveal(resource);capture("native-gallery");resource.tap()
        let design=app.buttons["封面设计"];XCTAssertTrue(design.waitForExistence(timeout:10));design.tap()
        XCTAssertTrue(app.navigationBars["封面设计"].waitForExistence(timeout:10));capture("native-editor-initial");let spatial=app.buttons["Spatial"];reveal(spatial,in:app.collectionViews.firstMatch);spatial.tap();capture("native-editor-spatial")
        let primary=app.textFields["cover-primary"];reveal(primary,in:app.collectionViews.firstMatch);primary.tap();primary.typeText("#777777")
        let title=app.descendants(matching:.any).matching(NSPredicate(format:"identifier == %@ AND (elementType == %d OR elementType == %d)","cover-custom-title",XCUIElement.ElementType.textField.rawValue,XCUIElement.ElementType.textView.rawValue)).firstMatch;reveal(title,in:app.collectionViews.firstMatch);title.tap();title.typeText("Native cover QA")
        app.navigationBars["封面设计"].buttons["保存"].tap();XCTAssertTrue(design.waitForExistence(timeout:10));XCTAssertFalse(app.alerts.firstMatch.exists,"Cover Save must not add a blocking confirmation after persistence");capture("native-saved-detail")
        design.tap();XCTAssertTrue(app.navigationBars["封面设计"].waitForExistence(timeout:10));reveal(spatial,in:app.collectionViews.firstMatch);XCTAssertTrue(spatial.isSelected);reveal(primary,in:app.collectionViews.firstMatch);XCTAssertEqual(primary.value as? String,"#777777");reveal(title,in:app.collectionViews.firstMatch);XCTAssertEqual(title.value as? String,"Native cover QA")
        title.tap();title.typeText(" cancelled");app.navigationBars["封面设计"].buttons["取消"].tap()
        design.tap();XCTAssertTrue(app.navigationBars["封面设计"].waitForExistence(timeout:10));reveal(title,in:app.collectionViews.firstMatch);XCTAssertEqual(title.value as? String,"Native cover QA","Cancel changed persisted title")
        let reset=app.buttons["恢复自动封面"];reveal(reset,in:app.collectionViews.firstMatch);reset.tap();app.navigationBars["封面设计"].buttons["保存"].tap();XCTAssertTrue(design.waitForExistence(timeout:10))
        design.tap();XCTAssertTrue(app.navigationBars["封面设计"].waitForExistence(timeout:10));reveal(title,in:app.collectionViews.firstMatch);XCTAssertTrue(["","封面标题 · 沿用资源名"].contains(title.value as? String ?? ""));capture("native-editor-reset");app.navigationBars["封面设计"].buttons["取消"].tap()
    }
    private func assertRenderedSubtitle() throws {
        let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate
        try VNImageRequestHandler(cgImage:app.screenshot().image.cgImage!).perform([request])
        let text=(request.results ?? []).compactMap{$0.topCandidates(1).first?.string}.joined().uppercased().filter{$0.isLetter}
        XCTAssertTrue(text.contains("CUSTOMSUBTITLEQA"),"Saved custom subtitle must actually be painted in the code cover: \(text)")
    }
    func testActualCodeCoverSubtitle() throws {
        let resource=app.buttons.matching(NSPredicate(format:"label CONTAINS %@","Native Code QA")).firstMatch
        for _ in 0..<8{if resource.exists{break};app.swipeUp()};XCTAssertTrue(resource.waitForExistence(timeout:15));reveal(resource);resource.tap()
        let design=app.buttons["封面设计"];XCTAssertTrue(design.waitForExistence(timeout:10));design.tap()
        let subtitle=app.descendants(matching:.any).matching(NSPredicate(format:"identifier == %@ AND (elementType == %d OR elementType == %d)","cover-custom-subtitle",XCUIElement.ElementType.textField.rawValue,XCUIElement.ElementType.textView.rawValue)).firstMatch
        reveal(subtitle,in:app.collectionViews.firstMatch);subtitle.tap();subtitle.typeText("CUSTOM SUBTITLE QA")
        app.navigationBars["封面设计"].buttons["保存"].tap();XCTAssertTrue(design.waitForExistence(timeout:10));try assertRenderedSubtitle();capture("native-code-subtitle")
        design.tap();let legacy=app.buttons["原版 V5"],strip=app.scrollViews.containing(.button,identifier:"原版 V5").firstMatch;reveal(strip,in:app.collectionViews.firstMatch);for _ in 0..<5{if legacy.isHittable{break};strip.swipeLeft()};XCTAssertTrue(legacy.isHittable);legacy.tap();app.navigationBars["封面设计"].buttons["保存"].tap();XCTAssertTrue(design.waitForExistence(timeout:10));try assertRenderedSubtitle();capture("native-v5-code-subtitle")
        design.tap();let reset=app.buttons["恢复自动封面"];reveal(reset,in:app.collectionViews.firstMatch);reset.tap();app.navigationBars["封面设计"].buttons["保存"].tap()
    }

}
