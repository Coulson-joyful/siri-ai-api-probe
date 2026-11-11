// Appended to an isolated diagnostic app; configuration-only also runs on a physical device.
enum SimulatorCheckError: Error { case unexpectedOutput(String) }
@MainActor func runSimulatorAPICheck(_ probe: ProbeModel) async {
    probe.running = true
    probe.results = []
    let configurationOnly = ProcessInfo.processInfo.arguments.contains("--configuration-only")
    defer { probe.running = false; probe.current = "独立接口检查完成"; probe.save() }
    func record(_ id: String, _ api: String, _ use: String, _ status: String, _ output: String) {
        probe.add(id, api, configurationOnly ? "独立配置检查" : "模拟器独立检查", status, use, output)
    }
    if !configurationOnly {
     for (id, model) in [("system-default", SystemLanguageModel.default),
                        ("system-general", SystemLanguageModel(useCase: .general)),
                        ("system-tagging", SystemLanguageModel(useCase: .contentTagging))] {
        let caps = model.capabilities
        record(id, "SystemLanguageModel availability / supportsLocale / capabilities", "访问状态、语言与声明能力查询；不代表生成成功。", "查询可调用",
               "availability=\(model.availability); isAvailable=\(model.isAvailable); zh-Hans-CN=\(model.supportsLocale(Locale(identifier: "zh-Hans-CN"))); guidedGeneration=\(caps.contains(.guidedGeneration)); toolCalling=\(caps.contains(.toolCalling)); vision=\(caps.contains(.vision))")
     }
    }
    var options = GenerationOptions(samplingMode: .greedy, temperature: 0.2, maximumResponseTokens: 120, toolCallingMode: .required)
    assert(options.samplingMode == .greedy && options.temperature == 0.2 && options.maximumResponseTokens == 120 && options.toolCallingMode == .required)
    record("generation-options", "GenerationOptions.init / samplingMode / temperature / maximumResponseTokens / toolCallingMode", "设置生成策略、输出上限及工具调用要求；仅验证参数构造与读回。", "构造读写可调用", "samplingMode=greedy; temperature=0.2; maximumResponseTokens=120; toolCallingMode=required; assertions=passed")
    options.maximumResponseTokens = 80
    options.toolCallingMode = .disallowed
    options.samplingMode = .random(top: 5, seed: 7)
    assert(options.maximumResponseTokens == 80 && options.toolCallingMode == .disallowed && options.samplingMode == .random(top: 5, seed: 7))
    record("generation-options-mutation", "GenerationOptions field mutation", "检查参数字段确实可修改，不把模型前置阻断归到值类型参数。", "构造读写可调用", "maximumResponseTokens=80; toolCallingMode=disallowed; samplingMode=random(top:5,seed:7); assertions=passed")
    for (label, value) in [("light", ContextOptions.ReasoningLevel.light), ("moderate", .moderate), ("deep", .deep)] {
        let context = ContextOptions(includeSchemaInPrompt: true, reasoningLevel: value)
        assert(context.reasoningLevel == value && context.includeSchemaInPrompt == true)
        record("context-" + label, "ContextOptions.reasoningLevel", "配置 PCC 推理档位；该构造不向云端发送请求。", "构造读写可调用", "reasoningLevel=\(label); includeSchemaInPrompt=true; assertions=passed")
    }
    let prompt = Prompt("只回复数字 12。")
    let instructions = Instructions("按固定测试要求作答。")
    _ = prompt
    let session = LanguageModelSession(model: SystemLanguageModel.default, instructions: instructions)
    record("session-construct", "Prompt / Instructions / LanguageModelSession.init", "构造单次输入、会话指令和会话；没有发生成请求。", "构造可调用", "prompt=只回复数字 12。; instructions initialized; session initialized; isResponding=\(session.isResponding)")
    let answer = ShortAnswer(greeting: "你好")
    assert(answer.greeting == "你好")
    let schema = ShortAnswer.generationSchema
    record("generable-guide-schema", "@Generable / @Guide / generationSchema", "宏生成类型和字段说明；能建立类型与 schema 不代表模型已经生成该类型。", "宏与类型可调用", "member initialization=passed; greeting=你好; schema=\(schema.debugDescription)")
    let model = SystemLanguageModel.default
    let calls = ToolCalls()
    let directToolOutput = try? await FixedLookup(calls: calls).call(arguments: LookupArguments(key: "fixture"))
    assert(directToolOutput == "校验码：ORCHID-731")
    let directCalls = await calls.count
    assert(directCalls == 1)
    record("tool-direct-call", "Tool.call(arguments:) direct invocation", "只验证 App 自己实现的工具函数可执行；不代表模型发起了工具调用。", "App工具函数可调用", "key=fixture; calls=1; output=校验码：ORCHID-731; assertions=passed; invokedByModel=false")
    let image = UIGraphicsImageRenderer(size: CGSize(width: 128, height: 128)).image { c in
        UIColor.white.setFill(); c.fill(CGRect(x: 0, y: 0, width: 128, height: 128))
        UIColor.red.setFill(); c.fill(CGRect(x: 32, y: 32, width: 64, height: 64))
    }.cgImage!
    let attachment = Attachment(image)
    _ = attachment
    let profileSession = LanguageModelSession(profile: TestProfile(stage: 1))
    record("attachment-profile-construct", "Attachment.init / LanguageModelSession(profile:)", "构造图片附件及动态会话；未进行图片理解或动态生成。", "构造可调用", "image=128x128 white background red square; attachment initialized; profile session initialized; isResponding=\(profileSession.isResponding)")
    if configurationOnly {
        record("complete", "configuration-only completion", "仅执行本地参数、类型、会话、附件和工具函数构造检查；无模型请求、语音、权限或系统功能操作。", "完成", "all configuration assertions completed")
        return
    }
    if model.isAvailable {
        await probe.attempt("respond-fixed", "LanguageModelSession.respond", "实际生成") {
            let text = try await LanguageModelSession(model: model).respond(to: "甲比乙大两岁，乙十岁。甲是多少岁？只回复数字。", options: GenerationOptions(samplingMode: .greedy, maximumResponseTokens: 20)).content
            guard text.trimmingCharacters(in: .whitespacesAndNewlines) == "12" else { throw SimulatorCheckError.unexpectedOutput(text) }
            return "output=\(text); expected=12; assertion=passed"
        }
        await probe.attempt("stream-fixed", "streamResponse", "实际分段生成") {
            var count = 0; var text = ""
            for try await response in LanguageModelSession(model: model).streamResponse(to: "用一句中文描述雨后的花园。") { count += 1; text = response.content }
            guard count > 0 && !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw SimulatorCheckError.unexpectedOutput(text) }
            return "snapshots=\(count); output=\(text); nonempty assertion=passed; semantic quality=not graded"
        }
        await probe.attempt("structured-fixed", "respond(generating:)", "实际结构化生成") {
            let answer = try await LanguageModelSession(model: model).respond(to: "用简体中文问好。", generating: ShortAnswer.self).content
            guard !answer.greeting.isEmpty else { throw SimulatorCheckError.unexpectedOutput("empty greeting") }
            return "greeting=\(answer.greeting); type and nonempty assertions=passed; semantic quality=not graded"
        }
        await probe.attempt("model-tool-fixed", "Tool.call via model", "实际模型工具调用") {
            let modelCalls = ToolCalls()
            let text = try await LanguageModelSession(model: model, tools: [FixedLookup(calls: modelCalls)]).respond(to: "调用 fixedLookup，key=fixture；请返回它提供的校验码，不要猜。 ").content
            let count = await modelCalls.count
            guard count > 0 && text.contains("ORCHID-731") else { throw SimulatorCheckError.unexpectedOutput("calls=\(count); \(text)") }
            return "toolCalls=\(count); output=\(text); assertions=passed"
        }
        await probe.attempt("vision-fixed", "Attachment image understanding", "实际图片理解") {
            let text = try await LanguageModelSession(model: model).respond { "图片中心是什么颜色和形状？用中文回答。"; Attachment(image) }.content
            guard text.contains("红") && text.contains("方") else { throw SimulatorCheckError.unexpectedOutput(text) }
            return "output=\(text); red-square assertion=passed"
        }
        await probe.attempt("profile-fixed", "DynamicProfile generation", "实际动态会话") {
            let a = try await LanguageModelSession(profile: TestProfile(stage: 1)).respond(to: "当前阶段？").content
            let b = try await LanguageModelSession(profile: TestProfile(stage: 2)).respond(to: "当前阶段？").content
            guard a.contains("阶段一") && b.contains("阶段二") else { throw SimulatorCheckError.unexpectedOutput("\(a); \(b)") }
            return "stage1=\(a); stage2=\(b); assertions=passed"
        }
    } else {
        for api in ["respond", "streamResponse", "respond(generating:)", "Tool.call via model", "Attachment image understanding", "DynamicProfile generation", "GenerationOptions runtime effect", "@Guide generation effect"] {
            record("blocked-" + api, api, "需要前置模型可访问才可验证真实生成。", "前置模型未就绪，未执行生成", String(describing: model.availability))
        }
    }
    let pcc = PrivateCloudComputeLanguageModel()
    record("pcc", "PrivateCloudComputeLanguageModel.availability", "PCC 访问状态查询；本探针没有 PCC 专用权限，不发云端请求。", "查询可调用", "availability=\(pcc.availability); isAvailable=\(pcc.isAvailable); requestSent=false")
    for level in ["light", "moderate", "deep"] {
        record("pcc-" + level, "PCC reasoning " + level, "参数构造成功；PCC 推理效果仍需真实服务资格。", "前置模型未就绪，未执行生成", String(describing: pcc.availability))
    }
    record("writing-tools", "UIWritingToolsCoordinator.isWritingToolsAvailable", "查询系统写作工具当前是否可用。", "查询可调用", String(UIWritingToolsCoordinator.isWritingToolsAvailable))
    record("image-playground", "ImagePlaygroundViewController.isAvailable", "查询系统图片生成界面当前是否可用。", "查询可调用", String(ImagePlaygroundViewController.isAvailable))
    let speechAvailable = SpeechTranscriber.isAvailable
    let speechLocales = await SpeechTranscriber.supportedLocales
    let speechLocale = await SpeechTranscriber.supportedLocale(equivalentTo: Locale(identifier: "zh-CN"))
    record("speech-supported", "SpeechTranscriber.isAvailable / supportedLocales / supportedLocale", "系统语音资源查询，单独记录未匹配 locale；不是 Apple 文字模型。", "查询可调用", "isAvailable=\(speechAvailable); supportedLocales=\(speechLocales.map(\.identifier)); zh-CN=\(speechLocale?.identifier ?? "nil")")
    if let locale = speechLocale {
        let module = SpeechTranscriber(locale: locale, preset: .transcription)
        record("speech-assets", "AssetInventory.status", "检查具体语音模块的资源状态；不请求下载。", "查询可调用", String(describing: await AssetInventory.status(forModules: [module])))
    } else {
        record("speech-assets", "SpeechTranscriber transcription / AssetInventory", "没有匹配到中文模块，保留明确的前置失败记录。", "前置语言未支持，未执行转录", "supportedLocale(zh-CN)=nil; no transcription request")
    }
    let dictationLocale = await DictationTranscriber.supportedLocale(equivalentTo: Locale(identifier: "zh-CN"))
    record("dictation-supported", "DictationTranscriber.supportedLocale", "查询听写所需语言，不申请录音权限。", "查询可调用", "zh-CN=\(dictationLocale?.identifier ?? "nil")")
    if let locale = dictationLocale {
        let module = DictationTranscriber(locale: locale, preset: .shortDictation)
        let formats = await module.availableCompatibleAudioFormats
        record("dictation-formats", "DictationTranscriber.availableCompatibleAudioFormats", "核对现有听写失败是否缺少音频格式准备；不把格式报错写成接口未开放。", "查询可调用", "formats=\(formats.map(\.description)); resources=\(await AssetInventory.status(forModules: [module]))")
    }
    let languageStatus = await LanguageAvailability().status(from: Locale.Language(identifier: "en"), to: Locale.Language(identifier: "zh-Hans"))
    record("translation-status", "LanguageAvailability.status", "系统翻译语言对查询；不是千问或 Foundation Models 生成。", "查询可调用", String(describing: languageStatus))
    record("complete", "probe completion", "未运行 Siri AI、ChatGPT、账户操作或权限申请。", "完成", "all assertions completed")
}
