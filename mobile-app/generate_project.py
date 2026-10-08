#!/usr/bin/env python3
import hashlib,json,plistlib
from pathlib import Path
root=Path(__file__).resolve().parent
objects={}
def ident(name):return hashlib.sha1(name.encode()).hexdigest()[:24].upper()
def obj(name,value):key=ident(name);objects[key]=value;return key
def q(v):return json.dumps(v,ensure_ascii=False)
def encode(v,indent=0):
 if isinstance(v,dict):return '{\n'+''.join('  '*(indent+1)+q(k)+' = '+encode(value,indent+1)+';\n' for k,value in v.items())+'  '*indent+'}'
 if isinstance(v,list):return '('+','.join(encode(x,indent+1) for x in v)+')'
 return q(str(v))
shared=['Shared/SyncClient.swift','Shared/SyncMerge.swift','Shared/Library.swift','Shared/Archive.swift','Shared/iOSImage.swift','Shared/Codec.c','Shared/Codec.h']
refs={path:obj(path,{'isa':'PBXFileReference','lastKnownFileType':'sourcecode.swift' if path.endswith('.swift') else 'sourcecode.c.c' if path.endswith('.c') else 'sourcecode.c.h','path':path,'sourceTree':'<group>'}) for path in [*shared,'App/ShijiApp.swift','App/ComputerSync.swift','ShareExtension/ShareViewController.swift']}
refs['App/Assets.xcassets']=obj('assets-ref',{'isa':'PBXFileReference','lastKnownFileType':'folder.assetcatalog','path':'App/Assets.xcassets','sourceTree':'<group>'})
products=[obj('app-product',{'isa':'PBXFileReference','explicitFileType':'wrapper.application','path':'Shiji.app','sourceTree':'BUILT_PRODUCTS_DIR'}),obj('extension-product',{'isa':'PBXFileReference','explicitFileType':'wrapper.app-extension','path':'ShijiShare.appex','sourceTree':'BUILT_PRODUCTS_DIR'})]
product_group=obj('products',{'isa':'PBXGroup','children':products,'name':'Products','sourceTree':'<group>'})
group=obj('group',{'isa':'PBXGroup','children':[*refs.values(),product_group],'sourceTree':'<group>'})
def configurations(label,app):
 result=[]
 for name in ['Debug','Release']:
  settings={'PRODUCT_NAME':'Shiji' if app else 'ShijiShare','PRODUCT_BUNDLE_IDENTIFIER':'local.silver.shiji.mobile' if app else 'local.silver.shiji.mobile.share','SHIJI_APP_GROUP':'group.local.silver.shiji','IPHONEOS_DEPLOYMENT_TARGET':'17.0','SWIFT_VERSION':'5.0','SWIFT_OBJC_BRIDGING_HEADER':'Shared/Codec.h','OTHER_LDFLAGS':['$(inherited)','-lz'],'TARGETED_DEVICE_FAMILY':'1','SDKROOT':'iphoneos','SUPPORTED_PLATFORMS':'iphoneos iphonesimulator','CODE_SIGN_STYLE':'Automatic','CODE_SIGN_ENTITLEMENTS':'App/Shiji.entitlements' if app else 'ShareExtension/Share.entitlements','INFOPLIST_FILE':'App/Info.plist' if app else 'ShareExtension/Info.plist','GENERATE_INFOPLIST_FILE':'NO','MARKETING_VERSION':'1.0.0','CURRENT_PROJECT_VERSION':'1','SWIFT_OPTIMIZATION_LEVEL':'-Onone' if name=='Debug' else '-O','CLANG_ENABLE_MODULES':'YES','ENABLE_USER_SCRIPT_SANDBOXING':'YES'}
  if not app:settings.update({'APPLICATION_EXTENSION_API_ONLY':'YES','SKIP_INSTALL':'YES'})
  else:settings.update({'ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME':'AccentColor','ASSETCATALOG_COMPILER_APPICON_NAME':'AppIcon'})
  result.append(obj(label+name,{'isa':'XCBuildConfiguration','name':name,'buildSettings':settings}))
 return obj(label+'configs',{'isa':'XCConfigurationList','buildConfigurations':result,'defaultConfigurationName':'Release','defaultConfigurationIsVisible':'0'})
ext_id=ident('extension-target');app_id=ident('app-target')
for label,app,product in [('app',True,products[0]),('extension',False,products[1])]:
 buildfiles=[obj(label+'build-'+path,{'isa':'PBXBuildFile','fileRef':refs[path]}) for path in [*[p for p in shared if not p.endswith(".h")],*(['App/ShijiApp.swift','App/ComputerSync.swift'] if app else ['ShareExtension/ShareViewController.swift'])]]
 sources=obj(label+'sources',{'isa':'PBXSourcesBuildPhase','buildActionMask':'2147483647','files':buildfiles,'runOnlyForDeploymentPostprocessing':'0'})
 frameworks=obj(label+'frameworks',{'isa':'PBXFrameworksBuildPhase','buildActionMask':'2147483647','files':[],'runOnlyForDeploymentPostprocessing':'0'})
 phases=[sources,frameworks];deps=[]
 if app:
  asset_build=obj('assets-build',{'isa':'PBXBuildFile','fileRef':refs['App/Assets.xcassets']})
  phases.append(obj('app-resources',{'isa':'PBXResourcesBuildPhase','buildActionMask':'2147483647','files':[asset_build],'runOnlyForDeploymentPostprocessing':'0'}))
  copyfile=obj('embed-extension-file',{'isa':'PBXBuildFile','fileRef':products[1],'settings':{'ATTRIBUTES':['RemoveHeadersOnCopy']}})
  phases.append(obj('embed-extension',{'isa':'PBXCopyFilesBuildPhase','buildActionMask':'2147483647','dstPath':'','dstSubfolderSpec':'13','files':[copyfile],'name':'Embed App Extensions','runOnlyForDeploymentPostprocessing':'0'}))
  proxy=obj('proxy',{'isa':'PBXContainerItemProxy','containerPortal':ident('project'),'proxyType':'1','remoteGlobalIDString':ext_id,'remoteInfo':'ShijiShare'})
  deps=[obj('dependency',{'isa':'PBXTargetDependency','target':ext_id,'targetProxy':proxy})]
 obj(label+'-target',{'isa':'PBXNativeTarget','name':'Shiji' if app else 'ShijiShare','productName':'Shiji' if app else 'ShijiShare','productReference':product,'productType':'com.apple.product-type.application' if app else 'com.apple.product-type.app-extension','buildConfigurationList':configurations(label,app),'buildPhases':phases,'buildRules':[],'dependencies':deps})
configs=[obj('project-'+name,{'isa':'XCBuildConfiguration','name':name,'buildSettings':{'CLANG_ENABLE_MODULES':'YES'}}) for name in ['Debug','Release']]
configlist=obj('project-configs',{'isa':'XCConfigurationList','buildConfigurations':configs,'defaultConfigurationName':'Release','defaultConfigurationIsVisible':'0'})
project=obj('project',{'isa':'PBXProject','attributes':{'LastUpgradeCheck':'2700','TargetAttributes':{app_id:{'SystemCapabilities':{'com.apple.ApplicationGroups.iOS':{'enabled':'1'}}},ext_id:{'SystemCapabilities':{'com.apple.ApplicationGroups.iOS':{'enabled':'1'}}}}},'buildConfigurationList':configlist,'compatibilityVersion':'Xcode 14.0','developmentRegion':'zh-Hans','hasScannedForEncodings':'0','knownRegions':['zh-Hans','en','Base'],'mainGroup':group,'productRefGroup':product_group,'projectDirPath':'','projectRoot':'','targets':[app_id,ext_id]})
p=root/'Shiji.xcodeproj';p.mkdir(exist_ok=True);(p/'project.pbxproj').write_text('// !$*UTF8*$!\n'+encode({'archiveVersion':'1','classes':{},'objectVersion':'56','objects':objects,'rootObject':project})+'\n')
scheme=p/'xcshareddata/xcschemes';scheme.mkdir(parents=True,exist_ok=True)
(scheme/'Shiji.xcscheme').write_text(f'''<?xml version="1.0" encoding="UTF-8"?><Scheme LastUpgradeVersion="2700" version="1.3"><BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{app_id}" BuildableName="Shiji.app" BlueprintName="Shiji" ReferencedContainer="container:Shiji.xcodeproj"/></BuildActionEntry></BuildActionEntries></BuildAction><LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{app_id}" BuildableName="Shiji.app" BlueprintName="Shiji" ReferencedContainer="container:Shiji.xcodeproj"/></BuildableProductRunnable></LaunchAction><ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/></Scheme>''')
common={'CFBundleIdentifier':'$(PRODUCT_BUNDLE_IDENTIFIER)','CFBundleExecutable':'$(EXECUTABLE_NAME)','CFBundleName':'$(PRODUCT_NAME)','CFBundleDisplayName':'拾集','CFBundleVersion':'$(CURRENT_PROJECT_VERSION)','CFBundleShortVersionString':'$(MARKETING_VERSION)','ShijiAppGroup':'$(SHIJI_APP_GROUP)','CFBundleInfoDictionaryVersion':'6.0','CFBundleDevelopmentRegion':'zh-Hans'}
for directory,app in [('App',True),('ShareExtension',False)]:
 info={**common,'CFBundlePackageType':'APPL' if app else 'XPC!'}
 if app:info.update({'LSRequiresIPhoneOS':True,'NSLocalNetworkUsageDescription':'在同一 Wi-Fi 与你配对的电脑同步收藏和素材。','CFBundleURLTypes':[{'CFBundleURLName':'ShijiComputerSync','CFBundleURLSchemes':['shiji-sync']}],'UILaunchScreen':{},'UISupportedInterfaceOrientations':['UIInterfaceOrientationPortrait','UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight'],'UIApplicationSceneManifest':{'UIApplicationSupportsMultipleScenes':False}})
 else:info.update({'NSExtension':{'NSExtensionPointIdentifier':'com.apple.share-services','NSExtensionPrincipalClass':'$(PRODUCT_MODULE_NAME).ShareViewController','NSExtensionAttributes':{'NSExtensionActivationRule':{'NSExtensionActivationSupportsWebURLWithMaxCount':1,'NSExtensionActivationSupportsWebPageWithMaxCount':1,'NSExtensionActivationSupportsText':True,'NSExtensionActivationSupportsImageWithMaxCount':1}}}})
 (root/directory/'Info.plist').write_bytes(plistlib.dumps(info));(root/directory/('Shiji.entitlements' if app else 'Share.entitlements')).write_bytes(plistlib.dumps({'com.apple.security.application-groups':['$(SHIJI_APP_GROUP)']}))
print(p)
