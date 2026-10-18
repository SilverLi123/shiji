import XCTest

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
}
