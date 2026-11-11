"""Explanations and test boundaries, kept separate from the original device evidence."""
NEWS = 'https://www.apple.com.cn/newsroom/2026/10/apple-intelligence-features-are-coming-to-users-in-china/'
FM = 'https://developer.apple.com/documentation/foundationmodels'
OPTIONS = FM + '/generationoptions'
EXPLANATIONS = {
 'SystemLanguageModel.default': 'App 访问 Apple 设备端文字模型的默认入口。开发者把提示词交给会话，再取得文字或指定格式的结果。它不是 Siri 聊天窗口，也不是千问扩展。',
 'SystemLanguageModel(.general)': 'useCase 是选择用途的参数；general 表示通用文字任务，例如摘要、改写、提取待办。它不是一个额外可选的模型品牌。',
 'SystemLanguageModel(.contentTagging)': 'contentTagging 是内容分类用途，例如给一篇日记提取主题、情绪、动作或物体标签。应检查返回的标签是否符合输入，而非只看请求是否完成。',
 'respond': '会话的一次生成方法。to 传入问题或材料，options 控制生成方式；调用方等待完整结果，再读取 content。例如把一段固定文字总结成一句话。',
 'streamResponse': '会话的分段生成方法。输入提示词后，程序持续接收生成过程中的结果，适合边生成边显示。应验证确实收到更新，以及最终文字是否正确。',
 '@Generable': '标在 Swift 数据类型上的宏，让模型按指定字段生成结果。例如定义 greeting 字段后，取回结构化数据，而非自行从一段回答里猜字段。generating 指定目标类型。',
 'Tool': '开发者声明模型可调用的 App 工具：name 和 description 解释用途，Arguments 定义参数，call(arguments:) 执行业务并返回结果。需要同时检查工具是否真正被调用、参数和回答是否正确。',
 'Attachment／图像理解': '把图片等附件连同问题传给支持该能力的模型。例如传入白底红色方块，询问颜色和形状。附件只是输入，不是生图接口，也不是另一套模型。',
 'DynamicProfile': '根据 App 当前状态切换会话的指令、工具或模型配置。适合多步骤流程；应改变测试阶段后再提问，检查回答是否跟着切换。',
 'PrivateCloudComputeLanguageModel': 'App 访问 Apple PCC 云端模型的入口，用于较长材料和较复杂推理。通过 LanguageModelSession 使用；它与中国区用户在 Siri 中选用千问是两个不同的接入途径。',
 'PCC light': 'reasoningLevel 的轻量推理选项。它设置云端请求的推理程度，不是另一个模型。需要与其他档位使用相同题目，实际比较结果及耗时。',
 'PCC moderate': 'reasoningLevel 的中等推理选项。用途同属 PCC 推理设置；选中此值并不保证某个固定速度或准确率。',
 'PCC deep': 'reasoningLevel 的深入推理选项。面向需要更多推理的请求；只有实际运行后，才能比较它与其他档位的差别。',
 '@AppIntent(.tool)／ToolIntent': '把 App 明确声明的动作提供给新版 Siri。动作参数由 App 定义，perform 执行操作；测试要检查自然语言匹配、参数、业务结果和 Siri 回复，不能只验证编译。',
 'SiriEvaluations／SiriService': '开发者用来自动评测 Siri 的框架。把预设请求交给 Siri 并记录表现；它是测试工具，不是供用户聊天的大模型。',
 'UIWritingToolsCoordinator／writingToolsBehavior': '把系统写作工具接到编辑界面。用户选中文字后执行校对、改写或摘要；behavior 控制编辑器接入行为。开发者不能据此指定或确认系统背后的模型。',
 'ImagePlaygroundViewController／imagePlaygroundSheet': '在 App 中打开系统图片生成界面，让用户描述并选择图片。它是系统交互界面，不是任意 App 可直接发请求的无界面生图服务。',
 'GenerationOptions.maximumResponseTokens': '限制本次回答最多输出多少 token，token 是模型处理文字的单位，不等于汉字数。本次设置 120；它不会授予模型访问权限。',
 'ContextOptions.reasoningLevel': '通过 light、moderate、deep 设置 PCC 请求的推理程度。它依赖可访问的云端模型，不能用来绕过模型或地区资格检查。',
 'availability／isAvailable／supportsLocale／capabilities': '这些查询分别回答当前能否访问、是否可用、是否支持某语言、声明支持哪些能力。查到 true 或某项能力，不等于已经获得生成结果；要继续执行对应任务。',
 'AssetInventory.status／assetInstallationRequest／downloadAndInstall': 'status 检查语音模块资源；assetInstallationRequest 取得需要安装的资源请求；downloadAndInstall 执行下载。完成后仍要用音频验证识别结果。',
 'SFSpeechURLRecognitionRequest.requiresOnDeviceRecognition': '布尔参数。设置 true 要求旧版语音识别在设备上处理指定音频；应核对实际返回文字，而非把授权成功当成识别成功。',
 'TranslationSession.prepareTranslation／translate': 'prepareTranslation 准备所需语言，translate 接收原文并返回译文。系统界面管理的会话和 installedSource:target: 直接创建的会话，必须分别测试。',
}
ADDITIONAL = [
 ('LanguageModelSession／Instructions／Prompt', '会话与输入', '会话保存这次交互；Instructions 描述持续遵守的要求，Prompt 是这次问题或材料。它们组织模型输入，本身不提供独立推理服务。'),
 ('GenerationOptions.temperature', '生成参数', '影响输出 token 的选择；用于调整生成行为，不代表答案正确率。nil 时采用模型默认设置。本轮没有做不同数值的对照。'),
 ('GenerationOptions.samplingMode', '生成参数', '设置生成时如何从候选 token 中选择输出。它与 temperature 同属生成策略，不是模型选项；本轮没有做策略对照。'),
 ('GenerationOptions.toolCallingMode', '工具调用参数', '设置模型使用工具时的要求。它控制会话内的工具调用行为，不会把没有提供给模型的 App 功能自动开放出来。'),
 ('@Guide', '结构化输出约束', '为 @Generable 的类型或字段提供描述和生成约束，帮助模型按预期填写数据；需要通过真实输出验证效果。'),
]

DEPENDENT = {'respond','streamResponse','@Generable','Tool','Attachment／图像理解','DynamicProfile','GenerationOptions.maximumResponseTokens','ContextOptions.reasoningLevel', *[r[0] for r in ADDITIONAL]}
ROOT_MODELS = {'SystemLanguageModel.default','SystemLanguageModel(.general)','SystemLanguageModel(.contentTagging)','PrivateCloudComputeLanguageModel'}
STATE_NAMES = {'ok':'已测试成功','partial':'已运行，需看结果','unavailable':'函数接口未开放','dependent':'前置未开放，无法测试','pending':'测试尚未完成','retired':'接口已停用'}
STATE_NAMES['not_ready']='模拟器条件未就绪'
STATE_NAMES['configured']='配置可调用，生成未验证'

def describe(name, old_state, result, limit):
    cloud = name.startswith('PCC ') or name.startswith('ContextOptions.') or name == 'PrivateCloudComputeLanguageModel'
    dependent = name in DEPENDENT or name.startswith('PCC ')
    source = OPTIONS if name.startswith('GenerationOptions.') else FM
    condition = '按所用系统框架的语言、资源及授权条件调用；不把语音或翻译接口成功当作大模型已开放。'
    if name.startswith(('Speech','Dictation','SFSpeech','AssetInventory')): source='https://developer.apple.com/documentation/speech'
    elif name.startswith('AVSpeech'): source='https://developer.apple.com/documentation/avfaudio/avspeechsynthesizer'
    elif name.startswith('Translation'): source='https://developer.apple.com/documentation/translation/translationsession'
    elif name.startswith('INPreferences'): source='https://developer.apple.com/documentation/sirikit'
    elif name.startswith('AppIntents'): source='https://developer.apple.com/documentation/appintents'
    elif name=='ImagePlaygroundViewController／imagePlaygroundSheet': source='https://developer.apple.com/documentation/imageplayground'
    elif name=='ImageCreator（旧接口）': source='https://developer.apple.com/news/?id=dz9wvq0r'
    stage = '已实际执行；结果及限制见下方。'
    cause = limit
    next_step = '新增场景需另测；不扩大本次固定样本的结论。'
    state = old_state
    if name in ROOT_MODELS or dependent:
        condition = ('需要 Apple Intelligence 支持设备、PCC 访问资格、专用 entitlement、受支持分发方式及网络。' if cloud else '公开 SDK 提供接入方式；当前模型必须通过 availability 检查，并支持本次使用的能力。')
        if dependent:
            state='dependent'
            stage='前置函数权限未开放，导致无法测试。没有执行该子函数的生成请求。'
            cause=('PCC' if cloud else 'SystemLanguageModel')+' 的前置检查返回 deviceNotEligible。这里指本次环境的模型访问条件未通过，没有证据证明该子函数被单独拒绝。'
            next_step='前置模型可访问后，用固定输入运行并核对输出；当前不能评价该子函数是否正常。'
        else:
            state='unavailable'
            stage='已查询可用性，未发送生成请求。'
            cause='本机返回 deviceNotEligible，说明当前接入条件未通过，返回值没有指出具体是哪项条件。'
            if cloud: cause+='测试 App 还缺 PCC 专用 entitlement，这是已经确认的另一项接入缺口。'
            next_step='先满足模型访问条件；不能靠反复运行子函数解决。具体地区、账户或设备原因仍需对照验证。'
        if name.startswith('GenerationOptions.') or name in {'ContextOptions.reasoningLevel','LanguageModelSession／Instructions／Prompt','@Generable','@Guide'}:
            state='partial';stage='SDK 编译通过；本轮真机尚未独立验证参数构造或字段读写，真实生成也未运行。'
            cause='参数／类型构造不需要模型访问资格，不能因生成被阻断就认定参数未开放。真机缺这组独立运行证据。'
            next_step='分别补参数构造读回、类型初始化和真实生成效果测试；模拟器的构造结果另列。'
    elif name == 'ImagePlaygroundViewController／imagePlaygroundSheet':
        state='unavailable'; stage='已查状态并实际打开系统界面；未进入图片生成。'
        cause='isAvailable=false，界面提示此 iPhone 不可用。确认本机当前未开放，未确定唯一原因。'
        next_step='待该系统入口可用后，再用固定描述测试生成结果。'
    elif name == 'ImageCreator（旧接口）':
        state='retired'; stage='按官方停用公告停止调用。'; cause='系统版本迁移问题，不是中国区单独限制。'; next_step='改用当前支持的图片生成界面。'
    elif name == 'SiriEvaluations／SiriService':
        state='dependent'; stage='前置函数权限未开放，导致无法测试；本轮不运行 Siri AI 评测。'
        condition='需要已开放的 Siri AI 运行环境，以及符合要求的界面测试目标。'
        cause='当前中国区 Beta 不包含 Siri AI。历史评测程序另有连接失败记录；这两件事分开，不能将连接报错当成开放状态证据。'
        next_step='等待对应地区和版本开放 Siri AI，再准备完整评测流程。'; source=NEWS
    elif old_state == 'pending':
        stage='测试未完成，不能据此判定接口未开放。'
        if name == 'SiriEvaluations／SiriService':
            cause='测试程序连接失败，未进入 Siri 场景；属于测试环境阻断。'; next_step='解决测试运行器连接或改用人工执行同一组请求，才能评测 Siri。'
        elif name == 'AVSpeechSynthesizer.write':
            cause='调用已开始，但本轮测试约 20 秒超时，尚未定位音频资源、回调或测试实现原因。'; next_step='单独检查音频回调与最小示例后再测；当前不是地区限制证据。'
        elif name == 'TranslationSession 直接初始化':
            cause='实际调用返回 notInstalled；此会话路径所需语言资源条件未通过。'; next_step='对照该初始化方式的资源要求重测，不能用另一条 UI 路径的成功替代。'
        else:
            cause='缺少本轮实际操作与输出。'; next_step='完成对应用户操作并保存完整结果。'
    elif name == '@AppIntent(.tool)／ToolIntent':
        state='unavailable'; stage='函数接口未开放（当前中国区 Siri AI 运行环境）；本轮不进行 Siri AI 测试。'
        cause='中国区首批 Beta 公告明确不包含新版 Siri AI，用户也确认手机尚无 Siri AI App。SDK 声明能编译不代表本机已提供服务。'
        condition='公开开发者预览 API 不等于当前地区提供新版 Siri AI。'; source=NEWS
        next_step='待中国区 Siri AI 和运行入口开放后再测；当前普通 Siri 快捷动作不能替代它。'
    elif name == 'UIWritingToolsCoordinator／writingToolsBehavior':
        if old_state=='ok':
            state='partial';stage='真机已查询、打开写作工具并运行改写预览。';cause=limit;next_step='用更长样本与不同操作继续评价质量，不把本次未变化的预览说成质量通过。'
        else:
            state='pending'; stage='本轮只完成 isWritingToolsAvailable=true 查询。';cause='缺少本轮改写或摘要的实际输入输出，尚未完成测试。';next_step='用固定文字运行一次改写和摘要，记录生成内容。'
        source=NEWS
    return dict(state=state,condition=condition,stage=stage,cause=cause,next_step=next_step,source=source)

def describe_simulator(name, info, records):
    """Never copy a physical-device outcome into a simulator result."""
    info=info.copy()
    info.update(state='pending',stage='本轮模拟器尚未完成该接口的运行验证。',cause='未取得此项的独立模拟器结果；不使用真机输出填充。',next_step='满足模拟器资源与服务条件后，用固定输入测试；需要真机资格的能力回到真机验证。')
    result='没有此项的独立模拟器输出。'
    by_id={r['id']:r for r in records}
    if name in ROOT_MODELS or name in DEPENDENT or name.startswith('PCC '):
        cloud=name.startswith('PCC ') or name.startswith('ContextOptions.') or name=='PrivateCloudComputeLanguageModel'
        key={'SystemLanguageModel(.general)':'system-general','SystemLanguageModel(.contentTagging)':'system-tagging'}.get(name,'pcc' if cloud else 'system-default')
        model_record=by_id.get(key)
        result=model_record.get('raw','') if model_record else '本轮缺少前置模型检查记录。'
        info.update(state='not_ready' if 'NotReady' in result else 'pending',stage='已查询前置模型状态，没有执行生成请求。' if model_record else '缺少前置检查。',cause='见实际返回；环境未就绪不能作为地区拒绝或子函数单独被拒绝的证据。')
        if name not in ROOT_MODELS: info['stage']='前置模型未就绪，导致无法测试该子函数。'
    mapping={
      'DictationTranscriber':'dictation','SFSpeechRecognizer（强制端侧）':'legacy-asr',
      'TranslationSession 直接初始化':'translation-direct',
      'SFSpeechURLRecognitionRequest.requiresOnDeviceRecognition':'legacy-asr',
      'UIWritingToolsCoordinator／writingToolsBehavior':'writing-tools',
      'ImagePlaygroundViewController／imagePlaygroundSheet':'image-playground',
      'SpeechTranscriber + SpeechAnalyzer':'speech-supported',
      'AssetInventory.status／assetInstallationRequest／downloadAndInstall':'speech-assets',
    }
    key=mapping.get(name)
    if name=='AVSpeechSynthesizer.write': key=next((k for k in by_id if k.startswith('tts-') and not k.endswith('-start')),None)
    if key in by_id:
        r=by_id[key];result=r.get('raw') or r['status']
        info['stage']='已在模拟器实际运行或查询，结果仅属于模拟器。'
        info['cause']='本轮模拟器调用未成功，需要检查资源或模拟器支持情况；没有地区拒绝证据。'
        if key in {'writing-tools','image-playground'}:
            info['state']='unavailable';info['cause']='模拟器可用性查询为 false；仅说明当前模拟器没有提供该入口。'
        elif r['status']=='执行成功': info['state']='partial';info['cause']='已收到输出，仍需按预期核对正确性。'
        if key in {'speech-supported','speech-assets'}:
            info.update(state='not_ready',cause='模拟器没有可用的中文 SpeechTranscriber 模块；已记录 locale=nil，不再无记录地跳过。')
    if name=='availability／isAvailable／supportsLocale／capabilities' and 'system-default' in by_id:
        info.update(state='ok',stage='已实际执行状态、语言与能力查询。',cause='查询可调用；返回的是模型未就绪，不代表生成成功。',next_step='模型就绪后再执行生成。');result=by_id['system-default']['raw']
    if name in {'@AppIntent(.tool)／ToolIntent','SiriEvaluations／SiriService'}:
        info.update(state='dependent',stage='本轮不测试 Siri AI。',cause='中国区首批 27.3 Beta 不包含 Siri AI。SDK 声明不代表模拟器已开放该服务。')
        result='未运行 Siri AI 请求。'
    if name=='ImageCreator（旧接口）':
        info.update(state='retired',stage='不调用已停用接口。',cause='全局版本迁移，不是中国区独有限制。');result='按官方停用公告处理。'
    return configuration_feedback(name,info,result,by_id)

def configuration_feedback(name, info, result, by_id):
    configuration_key = None
    if name.startswith('GenerationOptions.'): configuration_key='generation-options'
    elif name=='ContextOptions.reasoningLevel': configuration_key='context-light'
    elif name=='LanguageModelSession／Instructions／Prompt': configuration_key='session-construct'
    elif name in {'@Generable','@Guide'}: configuration_key='generable-guide-schema'
    elif name=='Tool': configuration_key='tool-direct-call'
    elif name in {'Attachment／图像理解','DynamicProfile'}: configuration_key='attachment-profile-construct'
    elif name.startswith('PCC '): configuration_key='context-'+name.split()[-1]
    if configuration_key in by_id and '可调用' in by_id[configuration_key].get('status',''):
        info=info.copy()
        r=by_id[configuration_key]
        info.update(state='configured',condition='参数、类型和普通业务函数可独立构造或执行；真实模型生成和模型选工具另需前置模型可访问。',stage='独立 Swift 探针已执行配置、构造或业务函数断言；未执行模型生成。',cause='配置／类型／普通函数可以运行。只有真实生成、模型选工具或参数对回答的影响仍依赖模型就绪。',next_step='模型可访问后再验证真实生成效果，不重复把配置构造标为未开放。')
        result=r.get('raw','')
    return info,result

def physical_model_feedback(name, info, result, records):
    by_id={r['id']:r for r in records}
    if name in ROOT_MODELS or name in DEPENDENT or name.startswith('PCC '):
        key={'SystemLanguageModel(.general)':'system-general','SystemLanguageModel(.contentTagging)':'system-tagging'}.get(name,'pcc' if name.startswith(('PCC ','ContextOptions.')) or name=='PrivateCloudComputeLanguageModel' else 'system-default')
        record=by_id.get(key)
        if record:
            info=info.copy();result=record['raw']
            unavailable='isAvailable=false' in result
            info['state']=('unavailable' if name in ROOT_MODELS else 'dependent') if unavailable else 'pending'
            info['stage']='本轮真机已执行访问状态查询；'+('没有执行生成请求。' if unavailable else '需核对真实生成记录。')
            info['cause']='以前置模型实际返回为准；不能把未执行的子函数当作单独收到拒绝，也不由此推断唯一地区原因。'
            if key=='pcc':info['cause']+=' App 缺少 PCC 专用 entitlement 是另一个已确认的接入缺口。'
            if name not in ROOT_MODELS and unavailable:info['stage']='前置函数权限未开放，导致无法测试生成；这里指模型访问条件未通过。'
    return info,result
