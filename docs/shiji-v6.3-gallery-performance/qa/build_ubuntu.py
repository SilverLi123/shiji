"""Build disposable Ubuntu/Python3.12/Node24 CI reproduction image; no host runtime install."""
import hashlib,shutil,subprocess,tempfile,tarfile,platform
from pathlib import Path
from urllib.request import urlopen
version='24.21.0';arch='arm64' if platform.machine()=='arm64' else 'x64';name=f'node-v{version}-linux-{arch}.tar.xz';url=f'https://nodejs.org/dist/v{version}/'
archive=Path('/tmp/shiji-v63-node-linux.tar.xz');checks=Path('/tmp/shiji-v63-node-shasums.txt')
if not archive.exists():
 with urlopen(url+name,timeout=60) as source,archive.open('wb') as target:shutil.copyfileobj(source,target)
if not checks.exists():
 with urlopen(url+'SHASUMS256.txt',timeout=30) as source:checks.write_bytes(source.read())
expected=next(line.split()[0] for line in checks.read_text().splitlines() if line.split()[-1]==name)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected,'Official Node digest mismatch'
root=Path(tempfile.mkdtemp(prefix='shiji-v63-docker-'))
with tarfile.open(archive) as tar:
 for member in tar.getmembers():
  assert not member.name.startswith('/') and '..' not in Path(member.name).parts
 tar.extractall(root)
(root/name.removesuffix('.tar.xz')).rename(root/'node-distribution')
shutil.copy2(Path(__file__).with_name('ubuntu.Dockerfile'),root/'Dockerfile')
print(f'Node {version} linux-{arch} sha256={expected}; context={root}',flush=True)
subprocess.run(['docker','build','--platform','linux/'+('arm64' if arch=='arm64' else 'amd64'),'-t','shiji-v63-ubuntu-qa',str(root)],check=True)
