"""Real XCUITest of the unchanged app architecture in a disposable QA copy/device.
No launch-time fake screen, test-only resource model, real pairing or formal AppGroup.
"""
import argparse,json,plistlib,runpy,shutil,signal,subprocess,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
QA=REPO/'mobile-app/dist/v64-native-qa'
PREFIX='local.silver.shiji.v64.qa'
GROUP='group.local.silver.shiji.v64.qa'
def command(*args,**kwargs):return subprocess.run([str(a) for a in args],check=True,**kwargs)
def prepare():
 source=QA/'source';source.mkdir(parents=True,exist_ok=True)
 for name in ['App','Shared','ShareExtension','UITests']:shutil.copytree(REPO/'mobile-app'/name,source/name,dirs_exist_ok=True)
 shutil.copyfile(REPO/'mobile-app/generate_project.py',source/'generate_project.py')
 scope=runpy.run_path(str(source/'generate_project.py'));objects=scope['objects'];obj=scope['obj'];ident=scope['ident'];encode=scope['encode']
 for value in objects.values():
  settings=value.get('buildSettings',{});bundle=settings.get('PRODUCT_BUNDLE_IDENTIFIER','')
  if bundle.startswith('local.silver.shiji.mobile'):settings['PRODUCT_BUNDLE_IDENTIFIER']=bundle.replace('local.silver.shiji.mobile',PREFIX);settings['SHIJI_APP_GROUP']=GROUP
 ref=obj('cover-ui-test-file',{'isa':'PBXFileReference','lastKnownFileType':'sourcecode.swift','path':'UITests/CoverStudioTests.swift','sourceTree':'<group>'})
 build=obj('cover-ui-test-build',{'isa':'PBXBuildFile','fileRef':ref})
 product=obj('cover-ui-test-product',{'isa':'PBXFileReference','explicitFileType':'wrapper.cfbundle','path':'ShijiCoverUITests.xctest','sourceTree':'BUILT_PRODUCTS_DIR'})
 sources=obj('cover-ui-test-sources',{'isa':'PBXSourcesBuildPhase','buildActionMask':'2147483647','files':[build],'runOnlyForDeploymentPostprocessing':'0'})
 frameworks=obj('cover-ui-test-frameworks',{'isa':'PBXFrameworksBuildPhase','buildActionMask':'2147483647','files':[],'runOnlyForDeploymentPostprocessing':'0'})
 settings={'PRODUCT_BUNDLE_IDENTIFIER':PREFIX+'.UITests','PRODUCT_NAME':'ShijiCoverUITests','SWIFT_VERSION':'5.0','GENERATE_INFOPLIST_FILE':'YES','IPHONEOS_DEPLOYMENT_TARGET':'17.0','SDKROOT':'iphoneos','SUPPORTED_PLATFORMS':'iphoneos iphonesimulator','TARGETED_DEVICE_FAMILY':'1','TEST_TARGET_NAME':'Shiji','CODE_SIGNING_ALLOWED':'NO'}
 configs=[obj('cover-ui-'+name,{'isa':'XCBuildConfiguration','name':name,'buildSettings':settings}) for name in ['Debug','Release']]
 config=obj('cover-ui-config',{'isa':'XCConfigurationList','buildConfigurations':configs,'defaultConfigurationName':'Debug','defaultConfigurationIsVisible':'0'})
 proxy=obj('cover-ui-proxy',{'isa':'PBXContainerItemProxy','containerPortal':ident('project'),'proxyType':'1','remoteGlobalIDString':scope['app_id'],'remoteInfo':'Shiji'})
 dependency=obj('cover-ui-dependency',{'isa':'PBXTargetDependency','target':scope['app_id'],'targetProxy':proxy})
 target=obj('cover-ui-target',{'isa':'PBXNativeTarget','name':'ShijiCoverUITests','productName':'ShijiCoverUITests','productReference':product,'productType':'com.apple.product-type.bundle.ui-testing','buildConfigurationList':config,'buildPhases':[sources,frameworks],'buildRules':[],'dependencies':[dependency]})
 objects[ident('group')]['children'].append(ref);objects[ident('products')]['children'].append(product);objects[ident('project')]['targets'].append(target)
 objects[ident('project')]['attributes']['TargetAttributes'][target]={'TestTargetID':scope['app_id'],'CreatedOnToolsVersion':'27.0'}
 project=source/'Shiji.xcodeproj';(project/'project.pbxproj').write_text('// !$*UTF8*$!\n'+encode({'archiveVersion':'1','classes':{},'objectVersion':'56','objects':objects,'rootObject':ident('project')})+'\n')
 reference=f'<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{target}" BuildableName="ShijiCoverUITests.xctest" BlueprintName="ShijiCoverUITests" ReferencedContainer="container:Shiji.xcodeproj"/>'
 scheme=project/'xcshareddata/xcschemes/Shiji.xcscheme';text=scheme.read_text();text=text.replace('</BuildActionEntries>',f'<BuildActionEntry buildForTesting="YES" buildForRunning="NO" buildForProfiling="NO" buildForArchiving="NO" buildForAnalyzing="NO">{reference}</BuildActionEntry></BuildActionEntries>');text=text.replace('<LaunchAction',f'<TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO">{reference}</TestableReference></Testables></TestAction><LaunchAction');scheme.write_text(text)
 info=source/'App/Info.plist';data=plistlib.loads(info.read_bytes());data['CFBundleDisplayName']='拾集 Cover QA';info.write_bytes(plistlib.dumps(data))
 return source

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--baseline',action='store_true');parser.add_argument('--subtitle-only',action='store_true');args=parser.parse_args()
 source=prepare()
 if args.baseline:(source/'App/ShijiApp.swift').write_bytes(subprocess.check_output(['git','show','31eeea2:mobile-app/App/ShijiApp.swift'],cwd=REPO))
 state=QA/'device.json'
 if state.exists():udid=json.loads(state.read_text())['udid']
 else:
  runtimes=json.loads(subprocess.check_output(['xcrun','simctl','list','runtimes','-j']))['runtimes'];runtime=next(r['identifier'] for r in runtimes if r.get('isAvailable') and r.get('platform')=='iOS')
  udid=subprocess.check_output(['xcrun','simctl','create','Shiji V6.4 Cover QA','com.apple.CoreSimulator.SimDeviceType.iPhone-17',runtime],text=True).strip();state.write_text(json.dumps({'udid':udid,'bundle':PREFIX,'group':GROUP}))
 devices=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','-j']))['devices'];assert any(d['udid']==udid and d['name']=='Shiji V6.4 Cover QA' for rows in devices.values() for d in rows),'Refusing non-QA simulator'
 if args.prepare_only:print(source,udid,flush=True);return
 command('xcrun','simctl','boot',udid,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) if not any(d['udid']==udid and d['state']=='Booted' for group in json.loads(subprocess.check_output(['xcrun','simctl','list','devices','-j']))['devices'].values() for d in group) else None
 command('xcrun','simctl','bootstatus',udid,'-b',stdout=subprocess.DEVNULL)
 mode='before' if args.baseline else 'after';derived=QA/('build-'+mode);result=QA/('result-'+mode+'-'+str(int(time.time()))+'.xcresult')
 build=['xcodebuild','-project',source/'Shiji.xcodeproj','-scheme','Shiji','-configuration','Debug','-destination','id='+udid,'-derivedDataPath',derived,'CODE_SIGNING_ALLOWED=YES','CODE_SIGN_IDENTITY=-','ONLY_ACTIVE_ARCH=YES','SHIJI_BUNDLE_PREFIX='+PREFIX,'SHIJI_APP_GROUP='+GROUP]
 subprocess.run(['xcrun','simctl','terminate',udid,PREFIX+'.UITests.xctrunner'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
 print('Building isolated native QA',mode,udid,flush=True)
 command(*build,'build-for-testing')
 app=derived/'Build/Products/Debug-iphonesimulator/Shiji.app';assert plistlib.loads((app/'Info.plist').read_bytes())['CFBundleIdentifier']==PREFIX
 command('xcrun','simctl','install',udid,app);command('xcrun','simctl','launch',udid,PREFIX)
 for _ in range(100):
  ready=subprocess.run(['xcrun','simctl','get_app_container',udid,PREFIX,GROUP],capture_output=True,text=True)
  if ready.returncode==0:break
  time.sleep(0.1)
 else:raise RuntimeError('Isolated App Group did not initialize')
 command('xcrun','simctl','terminate',udid,PREFIX)
 group=Path(subprocess.check_output(['xcrun','simctl','get_app_container',udid,PREFIX,GROUP],text=True).strip());library=group/'Library';library.mkdir(exist_ok=True)
 # Real schema3 JSON resource, written only while this isolated app is stopped.
 record={'id':'native-cover-qa','title':'SHIJI Cover QA','kind':'website','url':'https://github.com/SilverLi123/shiji','category':'开发工具','language':'Swift · Python','tags':['New, exact'],'projects':[],'projectNotes':{},'description':'隔离原生封面验收','notes':'保留的原始备注','coverId':'','attachments':[],'createdAt':'2026-10-18T00:00:00Z','updatedAt':'2026-10-18T00:00:00Z','coverConfig':{'style':'developer','template':'b','imageSource':'poster'}}
 code={**record,'id':'native-code-qa','title':'Native Code QA','kind':'code','snippet':'let answer = 42','coverConfig':{'style':'developer','template':'a','imageSource':'poster'}}
 (library/'library.json').write_text(json.dumps({'version':1,'schemaVersion':3,'resources':[record,code],'collections':[],'collectionMeta':[],'smartCollections':[]},ensure_ascii=False))
 # Use the single XCUITest runner. Concurrent simctl recording can stall startup/teardown; successful runs retain PNG attachments.
 test_command=[*build,'-resultBundlePath',result,*(['-only-testing:ShijiCoverUITests/CoverStudioTests/testActualCodeCoverSubtitle'] if args.subtitle_only else []),'test-without-building']
 command(*test_command,timeout=300)

 actual=json.loads((library/'library.json').read_text())['resources'][0]
 assert actual['title']==record['title'] and actual['notes']==record['notes'] and actual['tags']==record['tags'];assert actual.get('coverConfig') is None or args.subtitle_only
 (QA/'native-results.json').write_text(json.dumps({'passed':True,'simulator':udid,'bundle':PREFIX,'result':str(result),'resource':actual},ensure_ascii=False,indent=2));print('PASS: actual native save/cancel/reset, source fields and isolated AppGroup readback',flush=True)
if __name__=='__main__':main()
