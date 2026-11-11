#!/bin/bash
set -euo pipefail
# Usage: DEVELOPER_DIR=/path/to/Xcode.app/Contents/Developer bash Scripts/run_simulator_api_check.sh BOOTED_SIMULATOR_ID [OUTPUT_JSON]
# Uses an isolated app copy, never replaces the user's main probe or modifies device settings.
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
simulator_id="${1:?Pass a booted iOS 27.3 simulator identifier}"
output_json="${2:-$repo_dir/Evidence/2026-11-11/Simulator-subagent-results.json}"
task_dir="$(mktemp -d /tmp/apple-ai-api-check.XXXXXX)"
export repo_dir task_dir
python3 - <<'PY'
import os, shutil
from pathlib import Path
source=Path(os.environ['repo_dir']); target=Path(os.environ['task_dir'])/'source'
shutil.copytree(source,target,ignore=shutil.ignore_patterns('.git','Evidence','__pycache__','report.html'))
p=target/'SiriAIProbe/ExtendedTests.swift';s=p.read_text()
start=s.index('    func runExtended() async {');end=s.index('    func recognizeFixture(',start)
s=s[:start]+'    func runExtended() async { await runSimulatorAPICheck(self) }\n\n'+s[end:]
s+='\n'+(source/'Scripts/SimulatorAPICheck.swift').read_text()
p.write_text(s)
PY
xcodebuild -project "$task_dir/source/SiriAIProbe.xcodeproj" -scheme SiriAIProbe -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -derivedDataPath "$task_dir/build" PROBE_BUNDLE_ID=com.example.ai.subprobe CODE_SIGNING_ALLOWED=NO build >"$task_dir/build.log" 2>&1
xcrun simctl terminate "$simulator_id" com.example.ai.subprobe >/dev/null 2>&1 || true
xcrun simctl install "$simulator_id" "$task_dir/build/Build/Products/Debug-iphonesimulator/SiriAIProbe.app"
container_path="$(xcrun simctl get_app_container "$simulator_id" com.example.ai.subprobe data)"
export container_path output_json
python3 - <<'PY'
from pathlib import Path
import os
# Only discard the generated report owned by this isolated probe, preventing stale successes.
(Path(os.environ['container_path'])/'Documents/SiriAI-extended-results.json').unlink(missing_ok=True)
PY
xcrun simctl launch "$simulator_id" com.example.ai.subprobe --extended >"$task_dir/launch.log"
python3 - <<'PY'
from pathlib import Path
import os,json,time,re
p=Path(os.environ['container_path'])/'Documents/SiriAI-extended-results.json'
deadline=time.monotonic()+120
while time.monotonic()<deadline:
    try:
        data=json.loads(p.read_text())
        if any(r['id']=='complete' for r in data['results']):break
    except (FileNotFoundError,json.JSONDecodeError):pass
    time.sleep(1)
else:raise SystemExit('Probe did not complete in 120 seconds; inspect isolated build logs.')
data.update(date='2026-11-11',environment='simulator',buildSDK='27.3',osBuild='24C5037i',testMethod='Independent executable Swift probe, built and run in an isolated simulator app bundle',generationScope='Parameter and schema constructors are tested separately from generation. No generation bypasses model availability. No Siri AI, ChatGPT, microphone, permission requests, login, or paid service calls.')
for r in data['results']:
    r['timestamp']='2026-11-11'
    r['raw']=re.sub(r'/Users/[^/]+/[^\n ]*','[private path]',r['raw'])
    r['functionExecuted']=not r['status'].startswith('前置')
    r['executionStage']='实际代码执行' if r['functionExecuted'] else '前置检查后跳过生成'
    r['generationSent']=r.get('requestSent',False)
serialized=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
assert '/Users/' not in serialized
assert not re.search(r'[0-9A-F]{8}-[0-9A-F]{16}',serialized)
out=Path(os.environ['output_json']);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(serialized)
print(f'{len(data["results"])} records saved to {out}')
PY
printf 'Private build artifacts: %s\n' "$task_dir"
