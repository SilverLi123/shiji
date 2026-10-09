import UIKit
@main final class QADelegate:UIResponder,UIApplicationDelegate {
    var window:UIWindow?
    func application(_ application:UIApplication,didFinishLaunchingWithOptions options:[UIApplication.LaunchOptionsKey:Any]?=nil)->Bool {
        let w=UIWindow(frame:UIScreen.main.bounds);w.rootViewController=QAController();window=w;w.makeKeyAndVisible();return true
    }
}
final class QAController:UIViewController {
    override func viewDidLoad(){super.viewDidLoad();view.backgroundColor = .systemBackground
        let title=UILabel();title.text="SHIJI · Isolated Share QA";title.font = .preferredFont(forTextStyle:.title2)
        let stack=UIStackView(arrangedSubviews:[title]);stack.axis = .vertical;stack.spacing=24;stack.translatesAutoresizingMaskIntoConstraints=false
        for (index,name) in ["URL","Text","Image","Unsupported"].enumerated(){var config=UIButton.Configuration.filled();config.title="Share QA "+name;let button=UIButton(configuration:config,primaryAction:UIAction{[weak self]_ in self?.share(index)});stack.addArrangedSubview(button)}
        view.addSubview(stack);NSLayoutConstraint.activate([stack.centerYAnchor.constraint(equalTo:view.centerYAnchor),stack.leadingAnchor.constraint(equalTo:view.leadingAnchor,constant:24),stack.trailingAnchor.constraint(equalTo:view.trailingAnchor,constant:-24)])
    }
    func share(_ type:Int){let item:Any
        switch type {
        case 0:item=URL(string:"https://example.com/shiji-v21-share-qa")!
        case 1:item="SHIJI V2.1 QA — actual system text share, New, exact"
        case 2:item=UIGraphicsImageRenderer(size:CGSize(width:400,height:300)).image{c in UIColor.systemPurple.setFill();c.fill(CGRect(x:0,y:0,width:400,height:300));("SHIJI QA" as NSString).draw(at:CGPoint(x:40,y:130),withAttributes:[.font:UIFont.boldSystemFont(ofSize:32),.foregroundColor:UIColor.white])}
        default:item=Data([0x01,0x02])
        }
        let sheet=UIActivityViewController(activityItems:[item],applicationActivities:nil);sheet.popoverPresentationController?.sourceView=view;present(sheet,animated:true)
    }
}
