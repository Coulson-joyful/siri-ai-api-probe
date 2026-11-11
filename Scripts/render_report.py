"""Render the dated, self-contained report from public evidence; never reads raw device logs."""
from pathlib import Path
import json, html, re, base64
from report_content import NEWS, FM, EXPLANATIONS, ADDITIONAL, STATE_NAMES, describe, describe_simulator, configuration_feedback, physical_model_feedback
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'Evidence/2026-11-11'
e = lambda value: html.escape(str(value))
latest = json.loads((EVIDENCE/'Extended-results.json').read_text())
playback = json.loads((EVIDENCE/'Playback-results.json').read_text())
manual_path = EVIDENCE/'Manual-results.json'
manual = json.loads(manual_path.read_text()) if manual_path.exists() else {'siri': {'status':'本轮待人工确认'}, 'writingTools': {'status':'本轮待人工确认'}}
css = (ROOT/'Scripts/report.css').read_text()
sim = json.loads((EVIDENCE/'Simulator-results.json').read_text())
physical_code=json.loads((EVIDENCE/'Physical-code-results.json').read_text())
physical_configuration=json.loads((EVIDENCE/'Physical-configuration-results.json').read_text())
physical_configuration_by_id={r['id']:r for r in physical_configuration['results']}
sim_records = list(sim['results'])
subagent_path=EVIDENCE/'Simulator-subagent-results.json'
if subagent_path.exists():sim_records += json.loads(subagent_path.read_text())['results']
sources = [
('中国区 27.3 Beta 首批功能与千问接入（2026-10-31 公告）', NEWS),
('Apple 中国区产品说明','https://www.apple.com.cn/apple-intelligence/'),
('Foundation Models 框架与用途','https://developer.apple.com/documentation/foundationmodels'),
('内容标签：主题、情绪、动作和物体','https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel/usecase/contenttagging'),
('PCC：上下文、推理档位与请求条件','https://developer.apple.com/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute'),
('PCC 开发者资格与分发','https://developer.apple.com/private-cloud-compute/'),
('快捷指令四类模型与 Broad World Knowledge','https://support.apple.com/guide/shortcuts/use-apple-intelligence-in-shortcuts-tpg3vrvwmclv/ios'),
('多模态图像理解','https://developer.apple.com/documentation/foundationmodels/analyzing-images-with-multimodal-prompting'),
('动态会话与 Profile','https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles'),
('Siri 自定义工具、实体、屏幕上下文、跨 App 内容','https://developer.apple.com/documentation/appintents/bringing-custom-actions-and-content-to-siri'),
('SiriEvaluations','https://developer.apple.com/documentation/sirievaluations'),
('SpeechTranscriber','https://developer.apple.com/documentation/speech/speechtranscriber'),
('DictationTranscriber','https://developer.apple.com/documentation/speech/dictationtranscriber'),
('TranslationSession','https://developer.apple.com/documentation/translation/translationsession'),
('Writing Tools 协调器','https://developer.apple.com/documentation/uikit/uiwritingtoolscoordinator'),
('ImageCreator 终止公告','https://developer.apple.com/news/?id=dz9wvq0r'),
('Apple Intelligence 系统功能、语言和地区','https://support.apple.com/zh-cn/121115'),
('Siri AI 支持地区与语言','https://support.apple.com/en-us/127893'),
('Xcode SDK 对应版本','https://developer.apple.com/xcode/system-requirements')]
rows=[]
def row(name,kind,use,state,result,limit): rows.append((name,kind,use,state,result,limit))
row('SystemLanguageModel.default','端侧模型','短文本生成、摘要、改写、实体提取；可用于笔记摘要、游戏对话。','blocked','用 27.3 SDK 重测后，手机仍不允许这个 App 使用模型（deviceNotEligible），没有生成内容。','虽然系统说支持中文和这些功能，这次并没有拿到模型回答。')
row('SystemLanguageModel(.general)','端侧用途配置','通用文本理解与生成，例如把笔记整理成行动清单。','blocked','手机不允许使用，未生成内容（deviceNotEligible）。','不是另一个独立模型。')
row('SystemLanguageModel(.contentTagging)','端侧用途配置','输出主题、情绪、动作、物体等分类标签，例如日记标签。','blocked','手机不允许使用，未生成标签（deviceNotEligible）。','标签用途不等于通用长篇对话。')
for name,use in [('respond','返回完整文本回复。'),('streamResponse','逐步输出文本，例如边生成边显示摘要。'),('@Generable','生成 Swift 结构，例如标题、日期、待办字段。'),('Tool','调用 App 提供的查询函数，结合结果作答。'),('Attachment／图像理解','分析照片或文档图片；固定测试图为白底红色方块。'),('DynamicProfile','按 App 状态加载指令、工具和模型配置。')]:
 row(name,'模型调用机制',use,'blocked','手机不允许这个 App 使用模型，所以这项功能没有实际运行。','这是使用模型的一种方式。测试代码已写好，但还没有实际输出。')
row('PrivateCloudComputeLanguageModel','云端模型','较长文档分析、复杂推理、多轮对话。','blocked','手机显示不能使用（deviceNotEligible），App 也还缺 PCC 专用权限。','没有收到云端模型回答，仅凭这些结果还不能确定是不是地区限制。')
for level in ['light','moderate','deep']:
 row('PCC '+level,'云端推理配置','调整复杂问题的推理投入；可用于速度和结果质量对比。','blocked','PCC 目前无法使用，所以没有运行这个推理档位。','这是同一模型的不同推理设置。这次没有比较速度或回答质量。')
row('@AppIntent(.tool)／ToolIntent','Siri AI 动作接入','把自定义 App 动作暴露为 Siri 工具；可用于自然语言创建练习、查询记录。','partial','用 27.3 SDK 已做好接入代码，并成功装到手机。','还没确认 Siri 能否听懂不同说法、填对参数、找到 App 里的内容。')
row('SiriEvaluations／SiriService','开发者评测','用脚本对话检查 Siri 动作、参数、实体和回复。','pending','测试程序已做好，但还没连接上手机就退出了（code 74）。','正式测试还没开始。最初选错了测试类型，已按 Apple 要求改为界面测试；连接问题仍在。')
row('Siri → App Shortcut','标准动作路由','通过 Siri 执行 App 的明确动作，例如开始节拍器。','ok' if manual['siri'].get('passed') else 'pending',manual['siri']['status'],manual['siri'].get('detail','11 月 10 日用户反馈成功。这次还需重新确认；那句固定回复不是大模型生成的。'))
row('Writing Tools','系统写作界面','用户选中文字后润色、校对、摘要；适合笔记编辑器。','ok' if manual['writingTools'].get('passed') else 'partial',manual['writingTools']['status'],manual['writingTools'].get('detail','系统显示可以使用，之前也收到过成功反馈。这次还需记录实际改了哪些文字。'))
row('Image Playground','系统图片生成界面','在 App 中让用户生成并选择日记插图、贺卡配图。','blocked','isAvailable=false；实际打开界面提示“图乐园”在此 iPhone 上不可用。','本轮没有生成图片，不能据此定位唯一地区原因。')
row('SpeechTranscriber + SpeechAnalyzer','语音转文字','通用对话／音频转录、字幕。','ok','准备好所需语音文件后，识别出了“你好 ，这是中文语音接口测试。”','这段测试音频识别正确。还没测试真实会议、嘈杂环境或多人同时说话。')
row('DictationTranscriber','端侧听写','语音输入表单、口述笔记，兼容较老设备。','partial','返回：你好，就是中文语音接口测试','能识别出文字，但把“这是”听成了“就是”，内容并非完全正确。')
row('SFSpeechRecognizer（强制端侧）','旧版识别','旧工程中的短句输入和语音搜索。','partial','授权为 authorized；返回：你好就是中文语音接口测试','能识别出文字，同样把“这是”听成了“就是”。输入来自测试音频，没有录音。')
row('AVSpeechSynthesizer.speak','语音播放','朗读文章、播报测试结果、无障碍反馈。','ok','系统报告已经开始并完成朗读，耗时约 5 秒。','程序收到完成通知，但没有人工评价声音是否清楚、自然。')
row('AVSpeechSynthesizer.write','音频缓冲区合成','将文字生成音频文件或缓冲区，供处理和导出。','pending','三种中文声音都试了，等了约 20 秒仍没能完成音频文件生成。','直接朗读能完成，不代表导出音频也能完成。超时原因还没查清。')
row('TranslationSession UI 路径','端侧翻译','用户准备所需语言后翻译固定文本。','ok','同日先期 UI 下载后返回：雨后花园很安静。','这次成功来自同日较早的 27.2 SDK 测试。27.3 SDK 里另一种翻译调用方式仍提示语言未安装。')
row('TranslationSession 直接初始化','无界面翻译','已安装语言之间的后台文字翻译。','pending','27.3 SDK 显示支持英中翻译，但实际翻译时提示所需语言还没安装（notInstalled）。','在系统界面里翻译成功，不代表 App 在后台直接翻译也已经可用。')
row('INPreferences.siriAuthorizationStatus','旧 SiriKit 权限查询','检查旧 SiriKit 的 App 授权状态。','partial','配好普通 Siri 权限后，成功读到授权状态：用户还没作出选择（notDetermined）。','这次只查询了状态，没有申请授权，也没有测试旧版 Siri 的具体业务功能。')
for name,use in [('On-Device','快捷指令中的简单本地处理和转换，可用于离线工作流。'),('Cloud','快捷指令中由 PCC 处理复杂请求。'),('Cloud Pro','更长上下文和更大、更复杂的任务。'),('Extension Model','系统快捷指令中使用 ChatGPT；不是 App 的第三方 API 凭据。')]:
 row('Shortcuts '+name,'模型工作流选项',use,'pending','在快捷指令里搜索“模型”，没有找到相应操作，因此没能运行。','没有向这个模型发送问题，不能把它写成“调用后被拒绝”。')
row('Broad World Knowledge','快捷指令选项','为 Cloud／Cloud Pro 引入时事和现实世界背景。','pending','它依赖的模型操作没有出现，这项也没能运行。','不是额外独立模型。')
row('ImageCreator（旧接口）','已终止路径','原用于代码直接生成图片。','blocked','本轮不调用：Apple 明确其不再适用于 iOS 27 等系统。','按官方迁移到 Image Playground 界面或另选图片服务。')
state_names={'ok':'测试成功','partial':'只验证了一部分','blocked':'目前用不了','pending':'还没测成'}
display_names = {
 'SystemLanguageModel.default': '手机里的文字模型（默认入口）',
 'SystemLanguageModel(.general)': '通用文字处理',
 'SystemLanguageModel(.contentTagging)': '自动给内容打标签',
 'respond': '一次返回完整回答', 'streamResponse': '边生成边显示回答',
 '@Generable': '按指定格式生成结果', 'Tool': '让模型调用 App 功能',
 'Attachment／图像理解': '让模型看图', 'DynamicProfile': '随 App 状态调整模型用法',
 'PrivateCloudComputeLanguageModel': 'Apple 云端文字模型',
 '@AppIntent(.tool)／ToolIntent': '让新版 Siri 调用 App 功能',
 'SiriEvaluations／SiriService': '自动检查 Siri 有没有做对',
 'Siri → App Shortcut': '用 Siri 执行 App 快捷动作',
 'Writing Tools': '写作工具：润色、改写、摘要', 'Image Playground': '图乐园：生成图片',
 'SpeechTranscriber + SpeechAnalyzer': '把音频转成文字',
 'DictationTranscriber': '系统听写', 'SFSpeechRecognizer（强制端侧）': '旧版语音识别',
 'AVSpeechSynthesizer.speak': '直接朗读中文', 'AVSpeechSynthesizer.write': '把文字导出成音频',
 'TranslationSession UI 路径': '在系统界面里翻译',
 'TranslationSession 直接初始化': 'App 在后台直接翻译',
 'INPreferences.siriAuthorizationStatus': '查看旧版 Siri 授权状态',
 'Shortcuts On-Device': '快捷指令：手机本地模型', 'Shortcuts Cloud': '快捷指令：云端模型',
 'Shortcuts Cloud Pro': '快捷指令：处理更大任务的云端模型',
 'Shortcuts Extension Model': '快捷指令：ChatGPT 扩展模型',
 'Broad World Knowledge': '在回答中加入时事和现实背景',
 'ImageCreator（旧接口）': '旧版代码生图接口（已停用）'
}
# Developer APIs are kept separate from user-facing Shortcuts model choices.
users = [
('写作工具','编辑器中选中文字，选择写作工具','校对、改写和摘要；“创作”中的千问另行验证。',manual['writingTools']['status'],manual['writingTools']['detail']),
('系统文字翻译界面','测试 App 的“执行英中翻译”按钮','准备英语和中文资源，再翻译固定句子。','本机 27.3 构建实际成功','返回“雨后花园很安静。”。这是 Translation 系统界面，不等于电话／AirPods 实时翻译，也不证明千问可用。'),
]
users = [r for r in users if r[0] != '系统文字翻译界面']
users.insert(0,('千问问答（通过普通 Siri）','输入文字与 Siri 对话，明确要求千问回答','把问题交给中国区千问系统扩展回答。','真机成功，提供方标注为千问','输入“请千问计算17加25，只回复数字。”，返回 42。扩展已开启、账户已登录。只验证固定文字问答，不代表新版 Siri AI 或 App 直连 API 已开放。'))
developer_rows = [r for r in rows if not r[0].startswith('Shortcuts ') and r[0] != 'Broad World Knowledge']
new_names = {'Writing Tools':'UIWritingToolsCoordinator／writingToolsBehavior', 'Image Playground':'ImagePlaygroundViewController／imagePlaygroundSheet', 'Siri → App Shortcut':'AppIntents／AppShortcuts／perform'}
for index, r in enumerate(developer_rows):
 name,kind,use,state,result,limit=r
 if name=='TranslationSession UI 路径':
  result='27.3 SDK 构建里实际翻译成功：雨后花园很安静。'
  limit='点击系统翻译按钮，准备语言后得到结果。另一种直接调用方式仍报语言未安装，不能合并为所有翻译方式都成功。'
 if name in new_names:
  display_names[new_names[name]]= {'Writing Tools':'在 App 里接入写作工具','Image Playground':'在 App 里打开系统生图界面','Siri → App Shortcut':'把 App 动作接给 Siri 和快捷指令'}[name]
  name=new_names[name]
 developer_rows[index]=(name,kind,use,state,result,limit)
developer_rows += [
('availability／isAvailable／supportsLocale／capabilities','状态查询函数','分别查询当前能不能用、支持什么语言、声明了哪些能力。','ok','已经实际查询，完整值见下方记录。','查询成功只说明拿到了状态，不代表模型生成成功。'),
('GenerationOptions.maximumResponseTokens','生成参数','限制这次回答最多生成多少 token；测试代码设置为 120。','blocked','代码已能编译，模型不允许使用，未执行生成。','这个参数限制输出长度，不会改变设备是否有使用权限。'),
('ContextOptions.reasoningLevel','PCC 推理参数','选择 light、moderate、deep，调整回答前的推理投入。','blocked','三个档位都因 PCC 不可用而没有运行。','没有比较档位之间的速度或准确性。'),
('AssetInventory.status／assetInstallationRequest／downloadAndInstall','语音资源函数','检查并准备识别固定中文音频所需的文件。','ok','已把具体语音模块从 supported 准备为 installed，随后识别成功。','系统列出支持中文，不代表每个配置的所需文件都已准备好。'),
('SFSpeechURLRecognitionRequest.requiresOnDeviceRecognition','语音识别参数','设置为 true，要求旧版识别在手机上处理测试音频。','partial','设置后实际返回文字；“这是”被识别成“就是”。','没有使用麦克风，也没有测试联网识别。'),
('TranslationSession.prepareTranslation／translate','翻译函数','先准备语言，再把固定英语句子译成中文。','ok','27.3 SDK 系统界面路径成功，输出“雨后花园很安静。”。','installedSource:target: 直接创建翻译会话的方式仍返回 notInstalled。'),
]
display_names.update({'LanguageModelSession／Instructions／Prompt':'会话、持续指令与本次输入','GenerationOptions.temperature':'调整生成温度','GenerationOptions.samplingMode':'选择生成时的采样方式','GenerationOptions.toolCallingMode':'设置工具调用要求','@Guide':'说明字段的生成要求','availability／isAvailable／supportsLocale／capabilities':'检查模型能不能用','GenerationOptions.maximumResponseTokens':'限制回答长度','ContextOptions.reasoningLevel':'调整云端推理程度','AssetInventory.status／assetInstallationRequest／downloadAndInstall':'检查和下载语音文件','SFSpeechURLRecognitionRequest.requiresOnDeviceRecognition':'要求语音识别在手机上运行','TranslationSession.prepareTranslation／translate':'准备语言并执行翻译'})
for name,kind,use in ADDITIONAL:
 developer_rows.append((name,kind,use,'dependent','没有执行生成请求。','前置模型未通过访问检查。'))
state_names=STATE_NAMES
policy = [
('Apple Intelligence：在中国大陆购买的设备','Apple 的公开支持说明目前仍写明：在中国大陆购买的支持设备无法使用 Apple Intelligence。','这是 Apple 公布的开放范围；本次测试版中个别功能能用，不能据此推断所有功能都已开放。','https://support.apple.com/zh-cn/121115'),
('Apple Intelligence：境外购买的设备','设备在中国大陆使用，并且 Apple 账户地区也设为中国大陆时，官方说明目前无法使用 Apple Intelligence。','购买地、实际使用地区和账户地区是不同条件。报告没有切换账号或地区做对照。','https://support.apple.com/zh-cn/121115'),
('新版 Siri AI','官方说明：Apple 账户地区为中国大陆时，目前不能使用 Siri AI；iPhone 使用指南也列有中国大陆未开放说明。','它和能执行传统快捷动作的 Siri 不能混为一谈。此次未确认新版 AI 对话、屏幕理解或复杂操作已成功。','https://support.apple.com/en-us/127893'),
('PCC 云端模型','Apple 只在 Apple Intelligence 已开放的地区向符合条件的开发者提供 PCC。','App 还要取得专用权限并按支持的方式分发。本次既没通过设备检查，也缺专用权限，无法单独证明是地区拒绝。','https://developer.apple.com/private-cloud-compute/'),
('ChatGPT 系统扩展','Apple 说明该扩展只在 ChatGPT App 和服务提供的地区可用。','本次没有启用或运行扩展，也没有单独核验第三方服务账号资格。这里不把未测试写成已收到地区拒绝。','https://support.apple.com/zh-cn/121115'),
]
policy = [
('中国区首批 Apple Intelligence','10 月 31 日中国区公告：11 月 4 日起在开发者 Beta 开放首批功能，计划随 27.3 正式版推出。','修正旧版报告“全部尚未开放”的说法。第一标签只列本机已有可用证据的入口，官方列出的其他功能不冒充本机已验证。',NEWS),
('普通 Siri 与新版 Siri AI','首批更新包含 Siri 的部分改进和千问接入，但明确不包含新版 Siri AI 和其他下一代功能。','当前不运行 Siri AI 测试；手机没有新版 Siri AI App。普通 Siri、千问回答和 Siri AI 不能混用名称。',NEWS),
('千问扩展','中国区 Siri、写作工具和视觉智能可接入千问；需完成系统提供的启用与登录步骤。','本轮检查系统入口；不测 ChatGPT。系统接入千问不等于 Apple 全部内置模型都由千问替代，也不等于 App 获得千问 API。',NEWS),
('App 直接访问 Apple 设备端模型','公开 Foundation Models SDK 提供模型接入，实际仍需通过模型可用性检查。','真机返回 deviceNotEligible；不能由此断言中国区全部用户功能不可用。',FM),
('PCC 云端模型','开发者须满足 PCC 资格、专用 entitlement 和受支持的分发、地区等条件。','测试 App 缺专用权限，真机可用性检查也未通过；不能用千问扩展的开放代替 PCC 开放。','https://developer.apple.com/private-cloud-compute/'),
('图乐园和其他未确认功能','中国区首批功能有明确范围，不等于全球版全部功能。','图乐园在本机明确提示不可用；其他仅在官方清单出现、尚未检查本机的功能不放入“用户可直接调用”。',NEWS),
]
# Device errors and missing entitlements remain test feedback, not regional restrictions.
policy = policy[:3]
def section(number,title,ident):
 hidden = '' if ident == 'users' else ' hidden'
 return f'<section id="{ident}" class="report-panel" role="tabpanel" aria-labelledby="tab-{ident}" tabindex="0"{hidden}><div class="section-head"><span>{number}</span><h2>{e(title)}</h2></div>'
def table(headers,cls=''):
 return '<div class="table-wrap"><table class="'+cls+'"><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'
def cells(values):return '<tr>'+''.join('<td>'+e(v)+'</td>' for v in values)+'</tr>'
parts=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Apple Intelligence：用户可直接调用、开发者可调用与中国大陆限制不可用 · 2026-11-11</title><style>'+css+'</style></head><body><main>',
'<header><div class="topline"><span>APPLE INTELLIGENCE / TEST REPORT</span><span>2026.11.11 · XCODE 27.3</span></div><h1>Apple Intelligence，哪些能用？<br><span>用户可直接调用、开发者可调用与中国大陆限制不可用</span></h1><p class="lead">按“用户怎么用、开发者怎么接、哪些地区条件受限”分成三类。每项都写用途，并分清官方说明与这台手机的实际结果。</p><div class="meta"><span>国行 iPhone 16 Pro · iOS 27.3（24C5037i）</span><span>Xcode 27.3 beta（27C5020n）· iOS 27.3 SDK</span><span>测试日期：2026-11-11</span></div><div class="actions"><button onclick="window.print()">打印 / 另存 PDF</button></div><div class="environment-switch" role="group" aria-label="选择测试环境"><button type="button" data-env-select="physical" aria-pressed="true">真机 · iPhone 16 Pro</button><button type="button" data-env-select="simulator" aria-pressed="false">模拟器 · iOS 27.3</button></div><p id="environment-label" class="environment-label">当前查看：真机 · iPhone 16 Pro · iOS 27.3 Beta</p><div class="report-tabs" role="tablist" aria-label="报告分类"><button type="button" role="tab" id="tab-users" aria-controls="users" aria-selected="true" tabindex="0">用户可直接调用</button><button type="button" role="tab" id="tab-developers" aria-controls="developers" aria-selected="false" tabindex="-1">开发者可调用</button><button type="button" role="tab" id="tab-mainland" aria-controls="mainland" aria-selected="false" tabindex="-1">中国大陆限制不可用</button></div></header>',
 '<div class="verdict"><div class="kicker">本次报告范围</div><h2>测 Apple Intelligence；当前中国区 Beta 不包含新版 Siri AI。</h2><p>Apple 中国区公告已宣布首批功能与千问接入。系统功能开放，不等于 App 能直接调用 Apple 文字模型。真机模型访问检查未通过，后续生成函数没有运行；测试没完成的项目单独写明。</p><p class="small">报告更新：2026-11-11。历史真机、最新模拟器、官方说明和测试缺口分别记录，不把模拟器结果写成本机结论。</p></div>',
section('01','用户可直接调用','users'),
'<div data-environment="physical"><p>这里只列本机 27.3 Beta 已有可用证据的入口。系统报告支持和实际生成成功分开标明。没有验证开放的功能、国外版功能、Siri AI 和 ChatGPT 不放进本页。语音、朗读和 Translation 等关联系统接口单列在“开发者可调用”。</p>',table(['功能／模型选项','用户从哪里用','能做什么','这台手机的测试结果','还需要知道什么'],'user-table')]
parts += [cells(r) for r in users]
parts += ['</tbody></table></div><p class="small">千问单独检查系统扩展入口，只有得到实际返回才能列为本机测试成功；官方公布的首批功能范围请看“中国大陆限制不可用”。</p></div><div data-environment="simulator" hidden><div class="note"><strong>模拟器暂未验证出可直接完成的 Apple Intelligence 用户功能。</strong><p>千问系统扩展入口已经找到，但设置页为空白，尚未完成启用或取得回答。写作工具与图乐园查询均为 false。这里不展示真机翻译或朗读结果。</p></div></div>']
parts += ['</section>',section('02','开发者可调用','developers'),
'<p>先看接口用途和开放条件，再看本轮测试反馈。Apple 设备端模型、PCC、系统写作工具、千问扩展是不同入口；函数、参数和模型也分别说明。语音识别、朗读和 Translation 是关联系统接口，它们成功不代表 Apple 大模型已开放。</p><div class="note">“函数接口未开放”指当前本机无法访问，不表示 SDK 没有这个声明。子函数未执行时标明前置阻断；测试运行器、资源、回调或缺少操作造成的缺口，标为“测试尚未完成”。</div><input id="search" class="search" aria-label="搜索接口及用途" placeholder="搜索接口或用途，例如：摘要、语音、推理"><div class="filters"><button data-filter="all" aria-pressed="true">全部接口</button>'+''.join(f'<button data-filter="{key}" aria-pressed="false">{name}</button>' for key,name in state_names.items())+'</div><p id="count" class="small filter-count"></p><div class="api-list">']
callability=[]
for environment in ['physical','simulator']:
 for name,kind,use,state,result,limit in developer_rows:
  info=describe(name,state,result,limit)
  if environment=='simulator':info,result=describe_simulator(name,info,sim_records)
  else:
   info,result=physical_model_feedback(name,info,result,physical_code['results'])
   info,result=configuration_feedback(name,info,result,physical_configuration_by_id)
  state=info['state']
  callability.append(dict(environment=environment,api=name,kind=kind,description=EXPLANATIONS.get(name,use),result=result,**info))
  explanation=EXPLANATIONS.get(name,use)
  hidden=' hidden' if environment=='simulator' else ''
  environment_name='真机 · iPhone 16 Pro' if environment=='physical' else '模拟器 · iOS 27.3'
  parts.append(f'<article class="result-row" data-environment="{environment}" data-state="{state}"{hidden}><div class="api-heading"><div><h3>{e(display_names.get(name,name))}</h3><p class="technical">{e(name)} · {e(kind)}</p><p class="environment-tag">{environment_name}</p></div><span class="badge {state}">{state_names[state]}</span></div><p class="api-use">{e(explanation)}</p><p class="api-condition"><strong>开放条件：</strong>{e(info["condition"])} <a href="{e(info["source"])}">官方说明 ↗</a></p><details class="test-feedback"><summary>本轮测试反馈 · {state_names[state]}</summary><dl><dt>执行到哪</dt><dd>{e(info["stage"])}</dd><dt>实际记录</dt><dd>{e(result)}</dd><dt>原因判断</dt><dd>{e(info["cause"])}</dd><dt>还缺哪步</dt><dd>{e(info["next_step"])}</dd></dl></details></article>')
parts += ['</div><details><summary>测试范围与输入</summary><p>真机：国行 iPhone 16 Pro，iOS 27.3（24C5037i），Xcode 27.3 SDK。模拟器为独立的 27.3 环境，结果另列，不能替代真机或千问服务资格。</p><p>固定文字、合成音频和程序绘制的图片用于测试，没有读取私人文档、通讯录或相册。本轮不测试 Siri AI，也不测试 ChatGPT。</p></details>']
parts.append('<details><summary>官方首批功能中，本轮尚未完成的测试</summary><p>以下由中国区公告列入首批开放范围，但没有本轮完整的实操输出，因此不放进“用户可直接调用”，也不标成中国区不可用。</p><ul class="lists"><li>信息、电话、FaceTime 和 AirPods 实时翻译：把聊天或通话译成另一种语言；尚未准备通话及配套设备测试场景。</li><li>视觉智能：识别眼前物体、理解图像或屏幕内容；未完成固定测试图的系统入口问答。</li><li>照片消除、自然语言搜索、回忆影片：去除干扰物、按描述找照片、制作影片；未导入并运行标准相册样本。</li><li>智绘表情：按文字描述生成表情；未运行生成。</li><li>邮件优先、邮件摘要，以及邮件和信息的智能回复：未准备固定邮件／消息，不读取私人通信作样本。</li><li>通知摘要、首要通知、减少干扰：未构造固定通知场景。</li><li>备忘录音频及通话转录摘要：未准备录音、通话和摘要核对样本。</li><li>普通 Siri 的连续上下文等改进：本轮只完成千问固定文字问答，没有全面测试 Siri 的其他改进。</li></ul><p><a href="'+NEWS+'">Apple 中国区首批功能清单 ↗</a></p></details>')
parts.append('<details id="raw"><summary>查看详细测试记录（已去掉个人信息）</summary><p>用于核对具体返回值。程序收到完成通知，不代表人工已经听过声音；开始记录也不代表最终成功。</p>')
for name in ['Simulator-results.json','Simulator-UI-observations.json','Simulator-subagent-results.json','Physical-UI-current.json','Physical-configuration-results.json','Physical-code-results.json','Extended-results.json','Playback-results.json','Translation-UI-273-results.json','Translation-UI-results.json','UI-observations.json','Toolchain-and-signing.json','Manual-results.json']:
 path=EVIDENCE/name
 if path.exists():parts.append('<details data-environment="'+('simulator' if name.startswith('Simulator') else 'physical')+'"'+(' hidden' if name.startswith('Simulator') else '')+'><summary>'+e(name)+'</summary><pre>'+e(path.read_text())+'</pre></details>')
parts.append('<p class="small">原始崩溃日志、自动诊断包、个人签名和设备编号不公开。历史 11 月 10 日记录与本次 11 月 11 日记录分开保存。</p></details></section>')
parts += [section('03','中国大陆限制不可用','mainland'),
'<p>这里按 Apple 中国区公告说明开放边界：首批 Apple Intelligence 已进入 Beta，千问已接入；新版 Siri AI 和其他下一代功能不在这次范围内。这里只把官方地区范围作为地区结论。</p>',table(['涉及什么','Apple 官方怎么规定','本次结果如何理解','来源'],'policy-table')]
for name,rule,meaning,url in policy:
 parts.append('<tr>'+''.join('<td>'+e(v)+'</td>' for v in [name,rule,meaning])+'<td><a href="'+e(url)+'">Apple 官方说明</a></td></tr>')
parts += ['</tbody></table></div><div class="note"><strong>以下只是各环境的测试反馈，不属于已证实的中国大陆限制。</strong><ul class="lists"><li>真机返回 deviceNotEligible：没有说明具体是哪一个条件不满足；模拟器返回 modelNotReady／systemNotReady，是环境未就绪。</li><li>PCC 缺专用权限：是开发者接入条件，不能只按所在地区判断。</li><li>自动测试程序连不上手机：没有开始正式测试，不能据此判断 Siri 的地区政策。</li><li>音频文件生成超时、翻译语言未安装：需要分别排查。普通朗读和系统界面翻译已经成功。</li><li>旧 ImageCreator 被停用：这是 iOS 27 等版本的全局变化，不是中国大陆单独受限。</li></ul></div><p>中国区专项公告明确了这次 Beta 的范围。旧版报告仅凭通用支持页写“中国大陆全部尚未开放”不准确，已纠正；真机千问成功也不代表所有开发者模型接口都已开放。</p><details><summary>官方文档与用途说明来源</summary><ol class="sources">'+''.join(f'<li><a href="{e(url)}">{e(title)}</a></li>' for title,url in sources)+'</ol><p class="small">文档核对日期：2026-11-11。Siri AI 的较新使用指南列出更多语言；不影响这里引用的中国大陆地区条件。本文没有核对或切换用户的 Apple 账户地区。</p></details></section>',
'<footer><span>Apple Intelligence：用户可直接调用、开发者可调用与中国大陆限制不可用<br>2026-11-11 · Asia/Shanghai</span><span>单文件 HTML，可离线阅读和打印<br>官方链接需联网；后续系统更新可能改变结果</span></footer></main>',
'''<script>(()=>{let selected='all';let environment=new URL(location.href).searchParams.get('environment')==='simulator'?'simulator':'physical';const search=document.getElementById('search');const rows=[...document.querySelectorAll('.result-row')];const buttons=[...document.querySelectorAll('[data-filter]')];const environmentButtons=[...document.querySelectorAll('[data-env-select]')];function apply(){const q=search.value.trim().toLowerCase();let count=0;const total=rows.filter(row=>row.dataset.environment===environment).length;for(const node of document.querySelectorAll('[data-environment]'))if(!node.classList.contains('result-row'))node.hidden=node.dataset.environment!==environment;for(const row of rows){const show=row.dataset.environment===environment&&(selected==='all'||row.dataset.state===selected)&&row.textContent.toLowerCase().includes(q);row.hidden=!show;if(show)count++;}for(const button of environmentButtons)button.setAttribute('aria-pressed',String(button.dataset.envSelect===environment));document.getElementById('environment-label').textContent=environment==='physical'?'当前查看：真机 · iPhone 16 Pro · iOS 27.3 Beta':'当前查看：模拟器 · iPhone 16 Pro · iOS 27.3（24C5037i）';document.getElementById('count').textContent=`当前环境显示 ${count} / ${total} 项开发接口与参数`;}for(const button of buttons){button.addEventListener('click',()=>{selected=button.dataset.filter;for(const other of buttons)other.setAttribute('aria-pressed',String(other===button));apply();});}for(const button of environmentButtons)button.addEventListener('click',()=>{environment=button.dataset.envSelect;const url=new URL(location.href);url.searchParams.set('environment',environment);history.replaceState(null,'',url);apply();});search.addEventListener('input',apply);apply();})();
(()=>{const tabs=[...document.querySelectorAll('[role="tab"]')];const panels=[...document.querySelectorAll('[role="tabpanel"]')];function select(id,focus=false){if(!panels.some(panel=>panel.id===id))id='users';for(const panel of panels)panel.hidden=panel.id!==id;for(const tab of tabs){const active=tab.getAttribute('aria-controls')===id;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;if(active&&focus)tab.focus();}}for(const [index,tab]of tabs.entries()){tab.addEventListener('click',()=>{const id=tab.getAttribute('aria-controls');select(id);history.replaceState(null,'','#'+id);});tab.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;event.preventDefault();const id=tabs[next].getAttribute('aria-controls');select(id,true);history.replaceState(null,'','#'+id);});}function fromHash(){const hash=location.hash.slice(1);select(hash==='raw'?'developers':hash);}window.addEventListener('hashchange',fromHash);fromHash();})();</script></body></html>''']
output='\n'.join(parts)
from html.parser import HTMLParser
class Validate(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='a':self.links.append(a.get('href',''))
c=Validate();c.feed(output)
assert len(c.ids)==len(set(c.ids))
assert all(link[1:] in c.ids for link in c.links if link.startswith('#'))
assert output.count('<section')==output.count('</section>')==3
assert len(re.findall(r'<button[^>]+role="tab"', output))==3
assert len(re.findall(r'<section[^>]+role="tabpanel"', output))==3
assert output.count('tabindex="0" hidden')==2
assert 2*len(developer_rows)==output.count('class="result-row"')
assert output.count('class="test-feedback"') == 2*len(developer_rows)
assert not re.search(r'data-state="(?:blocked|all)"', output)
assert not re.search(r'/Users/[^/]+/|[0-9A-F]{8}-[0-9A-F]{16}', output)
(ROOT/'report.html').write_text(output)
(EVIDENCE/'Callability-matrix.json').write_text(json.dumps({'date':'2026-11-11','scope':'Apple Intelligence; Siri AI and ChatGPT excluded','results':callability},ensure_ascii=False,indent=2)+'\n')
print(f'Rendered 3 categories: {len(users)} user entries, {len(developer_rows)} developer entries, {len(policy)} regional rules; structure and privacy markers checked.')
