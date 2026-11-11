"""Render the dated, self-contained report from public evidence; never reads raw device logs."""
from pathlib import Path
import json, html, re, base64
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'Evidence/2026-11-11'
e = lambda value: html.escape(str(value))
latest = json.loads((EVIDENCE/'Extended-results.json').read_text())
playback = json.loads((EVIDENCE/'Playback-results.json').read_text())
manual_path = EVIDENCE/'Manual-results.json'
manual = json.loads(manual_path.read_text()) if manual_path.exists() else {'siri': {'status':'本轮待人工确认'}, 'writingTools': {'status':'本轮待人工确认'}}
css = (ROOT/'Scripts/report.css').read_text()
sources = [
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
# The report has exactly the three audiences requested by the user.
users = [
('Siri 的普通 App 快捷动作','对 Siri 说出 App 声明的快捷动作','例如开始节拍器、运行 App 里的连通性检查。',manual['siri']['status'],'11 月 10 日有成功反馈；这次的完整回复仍待确认。固定回复不含模型生成。'),
('新版 Siri AI 问答和操作','系统 Siri／Siri App','提问、理解屏幕内容、查找 App 内容，或组合操作。','还没完成新版能力测试','新的 App 工具已装到手机；没有新的对话、参数或跨 App 操作成功记录。普通快捷动作成功不能替代这些测试。'),
('写作工具','选中文字后选择写作工具','润色、改写、校对、摘要。',manual['writingTools']['status'],'系统显示支持；本轮仍待具体操作和输出，不能确定用了哪个模型。'),
('图乐园','图乐园 App，或 App 提供的系统生图界面','用文字描述创建图片。','这台手机目前用不了','在测试 App 中实际打开后，系统明确提示此 iPhone 不可用。'),
('快捷指令：On-Device','快捷指令中的“使用模型”操作','在手机上完成简单处理，例如短句转换；不需要联网。','没有找到模型操作','搜索“模型”没有结果，没有向这个选项发送问题。'),
('快捷指令：Cloud','快捷指令中的“使用模型”操作','由 Apple 云端模型处理较复杂的问题。','没有找到模型操作','没有运行请求，也没有速度、质量或用量结果。'),
('快捷指令：Cloud Pro','快捷指令中的“使用模型”操作','处理更长的材料和更大的任务。','没有找到模型操作','这是官方列出的选项，不代表当前手机上已经可选。'),
('快捷指令：Extension Model','快捷指令中的扩展模型选项','通过系统的 ChatGPT 扩展回答问题。','没有运行','没有登录、启用或调用扩展；安装 ChatGPT App 不等于系统扩展一定可用。'),
('Broad World Knowledge','Cloud／Cloud Pro 操作中的选项','让回答参考时事和现实世界背景。','没有运行','依赖的模型操作没有出现。这是一个选项，不是额外模型。'),
('系统翻译界面','在测试 App 中点击翻译按钮','准备好英语和中文后翻译句子。','27.3 SDK 实际翻译成功','输出“雨后花园很安静。”。这里验证的是测试 App 中的系统翻译界面，没有另外验收“翻译”App。'),
('系统键盘听写、朗读内容','键盘麦克风或系统无障碍朗读入口','把口述内容输入为文字，或读出屏幕文字。','这些系统入口还没逐项操作','开发者接口的转写和朗读已测试，结果放在第二类。不能把接口成功写成所有系统入口都已验收。'),
('照片编辑、搜索、回忆影片','照片等系统 App','编辑图片、用文字找照片、整理回忆。','未测试','没有读取个人相册，也没有为这些功能准备并运行测试内容。'),
('智绘表情、图像魔棒、信息背景','系统键盘、备忘录、信息等入口','生成表情、配图或聊天背景。','未测试','与图乐园有关的系统功能不等于同一个公开开发接口。'),
('邮件、信息和通知里的智能功能','邮件、信息、通知等界面','摘要、建议回复、投票建议、减少干扰。','未测试','各项语言、地区及内容条件需分别检查。'),
('实时翻译','信息、电话、FaceTime 或 AirPods','翻译聊天或通话内容。','未测试','文字翻译接口成功不代表通话、耳机翻译已经测试成功。'),
('Safari、日历、提醒事项、快捷指令里的智能操作','相应系统 App','整理浏览内容、用自然语言创建日程或提醒等。','未逐项测试','没有创建日程、提醒或运行这些系统智能操作。'),
('家庭、训练伙伴、钱包等智能功能','相应 App 及配套设备／服务','合并家居通知、搜索安防视频、运动指导或订单跟踪。','未测试','没有检查配套硬件、订阅、语言与地区条件。'),
]
# Developer APIs are kept separate from user-facing Shortcuts model choices.
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
display_names.update({'availability／isAvailable／supportsLocale／capabilities':'检查模型能不能用','GenerationOptions.maximumResponseTokens':'限制回答长度','ContextOptions.reasoningLevel':'调整云端推理程度','AssetInventory.status／assetInstallationRequest／downloadAndInstall':'检查和下载语音文件','SFSpeechURLRecognitionRequest.requiresOnDeviceRecognition':'要求语音识别在手机上运行','TranslationSession.prepareTranslation／translate':'准备语言并执行翻译'})
policy = [
('Apple Intelligence：在中国大陆购买的设备','Apple 的公开支持说明目前仍写明：在中国大陆购买的支持设备无法使用 Apple Intelligence。','这是 Apple 公布的开放范围；本次测试版中个别功能能用，不能据此推断所有功能都已开放。','https://support.apple.com/zh-cn/121115'),
('Apple Intelligence：境外购买的设备','设备在中国大陆使用，并且 Apple 账户地区也设为中国大陆时，官方说明目前无法使用 Apple Intelligence。','购买地、实际使用地区和账户地区是不同条件。报告没有切换账号或地区做对照。','https://support.apple.com/zh-cn/121115'),
('新版 Siri AI','官方说明：Apple 账户地区为中国大陆时，目前不能使用 Siri AI；iPhone 使用指南也列有中国大陆未开放说明。','它和能执行传统快捷动作的 Siri 不能混为一谈。此次未确认新版 AI 对话、屏幕理解或复杂操作已成功。','https://support.apple.com/en-us/127893'),
('PCC 云端模型','Apple 只在 Apple Intelligence 已开放的地区向符合条件的开发者提供 PCC。','App 还要取得专用权限并按支持的方式分发。本次既没通过设备检查，也缺专用权限，无法单独证明是地区拒绝。','https://developer.apple.com/private-cloud-compute/'),
('ChatGPT 系统扩展','Apple 说明该扩展只在 ChatGPT App 和服务提供的地区可用。','本次没有启用或运行扩展，也没有单独核验第三方服务账号资格。这里不把未测试写成已收到地区拒绝。','https://support.apple.com/zh-cn/121115'),
]
def section(number,title,ident):
 hidden = '' if ident == 'users' else ' hidden'
 return f'<section id="{ident}" class="report-panel" role="tabpanel" aria-labelledby="tab-{ident}" tabindex="0"{hidden}><div class="section-head"><span>{number}</span><h2>{e(title)}</h2></div>'
def table(headers,cls=''):
 return '<div class="table-wrap"><table class="'+cls+'"><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'
def cells(values):return '<tr>'+''.join('<td>'+e(v)+'</td>' for v in values)+'</tr>'
parts=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Siri AI：用户功能、开发接口与中国大陆限制 · 2026-11-11</title><style>'+css+'</style></head><body><main>',
'<header><div class="topline"><span>SIRI AI / DEVICE TEST REPORT</span><span>2026.11.11 · XCODE 27.3</span></div><h1>Siri AI，哪些能用？<br><span>用户功能、开发接口与中国大陆限制</span></h1><p class="lead">按“用户怎么用、开发者怎么接、哪些地区条件受限”分成三类。每项都写用途，并分清官方说明与这台手机的实际结果。</p><div class="meta"><span>国行 iPhone 16 Pro · iOS 27.3（24C5037i）</span><span>Xcode 27.3 beta（27C5020n）· iOS 27.3 SDK</span><span>测试日期：2026-11-11</span></div><div class="actions"><button onclick="window.print()">打印 / 另存 PDF</button></div><div class="report-tabs" role="tablist" aria-label="报告分类"><button type="button" role="tab" id="tab-users" aria-controls="users" aria-selected="true" tabindex="0">1. 用户直接用</button><button type="button" role="tab" id="tab-developers" aria-controls="developers" aria-selected="false" tabindex="-1">2. 开发者接入</button><button type="button" role="tab" id="tab-mainland" aria-controls="mainland" aria-selected="false" tabindex="-1">3. 中国大陆限制</button></div></header>',
'<div class="verdict"><div class="kicker">先看这次结果</div><h2>语音转文字、朗读中文和系统界面翻译能跑；测试 App 直接调用 Apple 大模型，目前还不行。</h2><p>手机模型返回“当前设备不符合使用条件”（deviceNotEligible），没有生成回答。新版 Siri 接入代码已做好并装到手机，但自动测试程序还没连接上手机，所以完整的新 Siri 操作仍未测成。</p><p class="small">清单没有全部测完。下面会直接标明“测试成功”“只验证了一部分”“目前用不了”或“还没测成”。没有把旧反馈当作这次的新结果，也没有把所有失败都归因于中国大陆限制。</p></div>',
section('01','用户可以直接用哪些模型或功能','users'),
'<p>这一类从手机上的入口讲：用户在哪里点、能拿它做什么。“系统里提供这个功能”和“你这台手机现在能用”分开写。</p>',table(['功能／模型选项','用户从哪里用','能做什么','这台手机的测试结果','还需要知道什么'],'user-table')]
parts += [cells(r) for r in users]
parts += ['</tbody></table></div><p class="small">快捷指令里的四个模型选项来自 Apple 官方说明。它们是用户工作流里的选项，不等于开发者可以直接选择的四个 Siri 内部模型。上表的系统功能不是本次已经全部试用过的功能。</p>']
image=EVIDENCE/'Shortcuts-model-action-search.png'
if image.exists():
 encoded=base64.b64encode(image.read_bytes()).decode()
 parts.append('<details><summary>查看手机截图：搜索“模型”没有找到操作</summary><figure><img src="data:image/png;base64,'+encoded+'" alt="目标 iPhone 的快捷指令动作搜索框中输入模型，结果列表为空。"><figcaption>只证明本次没有找到模型操作；没有向四个模型分别发送问题。</figcaption></figure></details>')
parts += ['</section>',section('02','开发者可以调用哪些模型、参数和函数','developers'),
'<p>这一类写 App 里的公开接入方式。函数存在、代码能编译、手机允许调用、实际返回了正确内容，是四件不同的事。这里列的是本次报告涉及并核对过的接口和主要参数，不是整套 SDK 的全部函数索引。</p><p>default、general 和 contentTagging 是同一个手机模型的不同用法。分段输出、指定格式、调用 App 功能，也不是额外模型。</p><input id="search" class="search" placeholder="搜索接口或用途，例如：摘要、语音、推理"><div class="filters"><button data-filter="all" aria-pressed="true">全部接口</button>'+''.join(f'<button data-filter="{key}" aria-pressed="false">{name}</button>' for key,name in state_names.items())+'</div><p id="count" class="small filter-count"></p>',table(['模型／接口／参数','能做什么','这次能用吗','手机上发生了什么','还不能确定什么'],'dev-table')]
for name,kind,use,state,result,limit in developer_rows:
 parts.append(f'<tr class="result-row" data-state="{state}"><td><strong>{e(display_names.get(name,name))}</strong><small>{e(name)} · {e(kind)}</small></td><td>{e(use)}</td><td><span class="badge {state}">{state_names[state]}</span></td><td>{e(result)}</td><td>{e(limit)}</td></tr>')
parts += ['</tbody></table></div><details><summary>测试设备、权限和版本说明</summary><p>手机已解锁，开发者模式已开启。新版测试使用 Xcode 27.3 和配套 iOS SDK；配套开发者磁盘镜像兼容且可用。App 的普通 Siri 签名权限已经配好，PCC 专用权限尚未取得。</p><p>输入只有固定句子、合成音频和程序画的测试图片，没有读取个人文档、相册、通讯录或录音。语音模块准备好所需文件后，才运行固定音频识别。翻译系统界面也已经在 27.3 SDK 构建中实际运行成功。</p><p>较早的 27.2 SDK 结果单独保留，不替代升级后的记录。没有更改手机地区、账号或系统语言。</p></details><details><summary>自动测试为什么没跑完</summary><p>SiriEvaluations 必须放在界面测试目标中。最初选错测试类型后已纠正；新目标可以做好并装到手机，但两次都在测试程序建立连接前退出（code 74），没有进入 Siri 对话场景。</p><p>新 Siri 工具能编译安装，不代表已经验证它能理解不同说法、填对参数、查到 App 内容或完成跨 App 操作。语音授权回调中另一个测试代码线程问题已经修复，之后识别成功；它没有被算作手机模型限制。</p></details>']
parts.append('<details id="raw"><summary>查看详细测试记录（已去掉个人信息）</summary><p>用于核对具体返回值。程序收到完成通知，不代表人工已经听过声音；开始记录也不代表最终成功。</p>')
for name in ['Extended-results.json','Playback-results.json','Translation-UI-273-results.json','Translation-UI-results.json','UI-observations.json','Toolchain-and-signing.json','Manual-results.json']:
 path=EVIDENCE/name
 if path.exists():parts.append('<details><summary>'+e(name)+'</summary><pre>'+e(path.read_text())+'</pre></details>')
parts.append('<p class="small">原始崩溃日志、自动诊断包、个人签名和设备编号不公开。历史 11 月 10 日记录与本次 11 月 11 日记录分开保存。</p></details></section>')
parts += [section('03','哪些在中国大陆尚未开放或受到限制','mainland'),
'<p>这里按 Apple 官方公布的产品开放范围整理。官方写明的地区限制、开发者权限不足、测试报错和还没测试，分别处理。</p>',table(['涉及什么','Apple 官方怎么规定','本次结果如何理解','来源'],'policy-table')]
for name,rule,meaning,url in policy:
 parts.append('<tr>'+''.join('<td>'+e(v)+'</td>' for v in [name,rule,meaning])+'<td><a href="'+e(url)+'">Apple 官方说明</a></td></tr>')
parts += ['</tbody></table></div><div class="note"><strong>以下问题不能直接写成“中国大陆禁止使用”。</strong><ul class="lists"><li>模型返回 deviceNotEligible：手机没有说明具体是哪一个条件不满足。</li><li>PCC 缺专用权限：是开发者接入条件，不能只按所在地区判断。</li><li>自动测试程序连不上手机：没有开始正式测试，不能据此判断 Siri 的地区政策。</li><li>音频文件生成超时、翻译语言未安装：需要分别排查。普通朗读和系统界面翻译已经成功。</li><li>旧 ImageCreator 被停用：这是 iOS 27 等版本的全局变化，不是中国大陆单独受限。</li></ul></div><p>你的测试版中能看到或操作的功能，可能与公开支持页面的描述不同。本报告保留两边的信息：官方怎么说、这台手机实际发生了什么。一次成功或一次报错，都不能代表所有中国大陆设备。</p><details><summary>官方文档与用途说明来源</summary><ol class="sources">'+''.join(f'<li><a href="{e(url)}">{e(title)}</a></li>' for title,url in sources)+'</ol><p class="small">文档核对日期：2026-11-11。Siri AI 的较新使用指南列出更多语言；不影响这里引用的中国大陆地区条件。本文没有核对或切换用户的 Apple 账户地区。</p></details></section>',
'<footer><span>Siri AI：用户功能、开发接口与中国大陆限制<br>2026-11-11 · Asia/Shanghai</span><span>单文件 HTML，可离线阅读和打印<br>官方链接需联网；后续系统更新可能改变结果</span></footer></main>',
'''<script>(()=>{let selected='all';const search=document.getElementById('search');const rows=[...document.querySelectorAll('.result-row')];const buttons=[...document.querySelectorAll('[data-filter]')];function apply(){const q=search.value.trim().toLowerCase();let count=0;for(const row of rows){const show=(selected==='all'||row.dataset.state===selected)&&row.textContent.toLowerCase().includes(q);row.hidden=!show;if(show)count++;}document.getElementById('count').textContent=`显示 ${count} / ${rows.length} 项开发接口与参数`;}for(const button of buttons){button.addEventListener('click',()=>{selected=button.dataset.filter;for(const other of buttons)other.setAttribute('aria-pressed',String(other===button));apply();});}search.addEventListener('input',apply);apply();})();
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
assert len(developer_rows)==output.count('class="result-row"')
assert all(len(re.findall('<td',r))==5 for r in re.findall(r'<tr class="result-row".*?</tr>',output,re.S))
assert not re.search(r'/Users/[^/]+/|[0-9A-F]{8}-[0-9A-F]{16}', output)
(ROOT/'report.html').write_text(output)
print(f'Rendered 3 categories: {len(users)} user entries, {len(developer_rows)} developer entries, {len(policy)} regional rules; structure and privacy markers checked.')
