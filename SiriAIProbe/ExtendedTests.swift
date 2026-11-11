import SwiftUI
import FoundationModels
import Speech
import AVFoundation
@preconcurrency import Translation
import ImagePlayground
import Intents

@Generable struct LookupArguments { var key: String }
actor ToolCalls {
    var count = 0
    func increment() { count += 1 }
}
struct FixedLookup: Tool {
    let name = "fixedLookup"
    let description = "查询测试条目对应的校验码。只有调用此工具才能知道正确答案。"
    let calls: ToolCalls
    func call(arguments: LookupArguments) async throws -> String {
        await calls.increment()
        return "校验码：ORCHID-731"
    }
}
struct TestProfile: LanguageModelSession.DynamicProfile {
    var stage: Int
    var body: some LanguageModelSession.DynamicProfile {
        if stage == 1 {
            LanguageModelSession.Profile { Instructions("只回复阶段一。") }
        } else {
            LanguageModelSession.Profile { Instructions("只回复阶段二。") }
        }
    }
}

@MainActor func deadline<T: Sendable>(_ seconds: Double, operation: @escaping @MainActor () async throws -> T) async throws -> T {
    try await withCheckedThrowingContinuation { continuation in
        var finished = false
        let operationTask = Task { @MainActor in
            do {
                let value = try await operation()
                guard !finished else { return }; finished = true
                continuation.resume(returning: value)
            } catch {
                guard !finished else { return }; finished = true
                continuation.resume(throwing: error)
            }
        }
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(seconds))
            guard !finished else { return }; finished = true
            operationTask.cancel()
            continuation.resume(throwing: ProbeModel.ProbeError.timeout)
        }
    }
}

extension ProbeModel {
    func attempt(_ id: String, _ api: String, _ category: String, seconds: Double = 35,
                 operation: @escaping @MainActor () async throws -> String) async {
        current = api
        add(id + "-start", api, category, "开始执行", "仅为进度记录，不代表成功。")
        let start = Date()
        do {
            let output = try await deadline(seconds, operation: operation)
            add(id, api, category, "执行成功", "使用固定测试输入。", "\(output)\nelapsedSeconds=\(Date().timeIntervalSince(start))", sent: true)
        } catch {
            add(id, api, category, "执行失败", error.localizedDescription,
                "\(String(reflecting: error)); elapsedSeconds=\(Date().timeIntervalSince(start))", sent: true)
        }
    }

    func runExtended() async {
        guard !running else { return }
        running = true; results = []
        UIApplication.shared.isIdleTimerDisabled = true
        defer { running = false; current = "扩展补测完成"; save(); UIApplication.shared.isIdleTimerDisabled = false }
        for (id, model) in [("system-default", SystemLanguageModel.default),
                            ("system-general", SystemLanguageModel(useCase: .general)),
                            ("system-tagging", SystemLanguageModel(useCase: .contentTagging))] {
            await testSystem(id, model: model)
        }
        let model = SystemLanguageModel.default
        let mechanisms = [("stream", "streamResponse"), ("tool", "Tool"), ("vision", "Attachment + image"), ("profile", "DynamicProfile")]
        if model.isAvailable {
            await attempt("stream", "streamResponse", "端侧生成") {
                var text = ""; var snapshots = 0
                for try await response in LanguageModelSession().streamResponse(to: "用一句话描述雨后的花园。") {
                    text = response.content; snapshots += 1
                }
                return "snapshots=\(snapshots); output=\(text)"
            }
            await attempt("tool", "Tool", "工具调用") {
                let calls = ToolCalls()
                let response = try await LanguageModelSession(tools: [FixedLookup(calls: calls)]).respond(to: "调用 fixedLookup 查询测试条目的校验码。")
                return "toolCalls=\(await calls.count); output=\(response.content)"
            }
            await attempt("vision", "Attachment + image", "图像理解") {
                let image = UIGraphicsImageRenderer(size: CGSize(width: 128, height: 128)).image { c in
                    UIColor.white.setFill(); c.fill(CGRect(x: 0, y: 0, width: 128, height: 128))
                    UIColor.red.setFill(); c.fill(CGRect(x: 32, y: 32, width: 64, height: 64))
                }.cgImage!
                let response = try await LanguageModelSession().respond {
                    "图片中心是什么颜色和形状？用一句中文回答。"
                    Attachment(image)
                }
                return response.content
            }
            await attempt("profile", "DynamicProfile", "动态会话") {
                let a = try await LanguageModelSession(profile: TestProfile(stage: 1)).respond(to: "现在是什么阶段？").content
                let b = try await LanguageModelSession(profile: TestProfile(stage: 2)).respond(to: "现在是什么阶段？").content
                return "stage1=\(a); stage2=\(b)"
            }
        } else {
            for (id, api) in mechanisms {
                add(id, api, "端侧模型能力", "前置阻断", "本轮端侧模型资格未通过，没有请求输出。", String(describing: model.availability))
            }
        }
        let pcc = PrivateCloudComputeLanguageModel()
        add("pcc", "PrivateCloudComputeLanguageModel", "云端模型", pcc.isAvailable ? "资格通过" : "资格不通过", "需要同时满足托管权限与受支持分发条件；本轮没有为账号申请新资格。", String(describing: pcc.availability))
        for (label, level) in [("light", ContextOptions.ReasoningLevel.light), ("moderate", .moderate), ("deep", .deep)] {
            if pcc.isAvailable {
                await attempt("pcc-" + label, "PCC reasoning " + label, "云端推理", seconds: 60) {
                    let response = try await LanguageModelSession(model: pcc).respond(to: "甲比乙大两岁，乙十岁。甲是多少岁？只回答年龄。", contextOptions: ContextOptions(reasoningLevel: level))
                    return response.content
                }
            } else {
                add("pcc-" + label, "PCC reasoning " + label, "云端推理", "前置阻断", "PCC 本轮资格未通过，未发送该档位请求。", String(describing: pcc.availability))
            }
        }
        add("writing-tools", "UIWritingToolsCoordinator", "写作工具", UIWritingToolsCoordinator.isWritingToolsAvailable ? "可用性为真" : "可用性为假", "实际改写另由系统 UI 验证。", String(UIWritingToolsCoordinator.isWritingToolsAvailable))
        add("image-playground", "ImagePlaygroundViewController", "图像生成", ImagePlaygroundViewController.isAvailable ? "可用性为真" : "可用性为假", "实际打开界面另行验证。", String(ImagePlaygroundViewController.isAvailable))

        // Test a prepackaged synthetic file; no microphone or personal recordings.
        let fixture = Bundle.main.url(forResource: "ASR-fixture", withExtension: "aiff")!
        if let locale = await SpeechTranscriber.supportedLocale(equivalentTo: Locale(identifier: "zh-CN")) {
            let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
            await attempt("speech-install", "AssetInventory.downloadAndInstall", "语音资源", seconds: 120) {
                let before = await AssetInventory.status(forModules: [transcriber])
                if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) { try await request.downloadAndInstall() }
                let after = await AssetInventory.status(forModules: [transcriber])
                return "before=\(before); after=\(after)"
            }
            if await AssetInventory.status(forModules: [transcriber]) == .installed {
                await attempt("asr-fixture", "SpeechAnalyzer + SpeechTranscriber", "语音转写") {
                    try await self.transcribe(url: fixture, transcriber: transcriber)
                }
            } else {
                add("asr-fixture", "SpeechAnalyzer + SpeechTranscriber", "语音转写", "资源阻断", "已尝试资源安装，但具体模块仍未安装就绪。", String(describing: await AssetInventory.status(forModules: [transcriber])))
            }
        }
        if let locale = await DictationTranscriber.supportedLocale(equivalentTo: Locale(identifier: "zh-CN")) {
            let transcriber = DictationTranscriber(locale: locale, preset: .shortDictation)
            await attempt("dictation", "SpeechAnalyzer + DictationTranscriber", "听写", seconds: 90) {
                if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) { try await request.downloadAndInstall() }
                let analyzer = SpeechAnalyzer(modules: [transcriber])
                let collect = Task {
                    var text = ""
                    for try await result in transcriber.results { text += String(result.text.characters) }
                    return text
                }
                do {
                    try await analyzer.start(inputAudioFile: AVAudioFile(forReading: fixture), finishAfterFile: true)
                    return try await collect.value
                } catch { collect.cancel(); await analyzer.cancelAndFinishNow(); throw error }
            }
        }
        // A speech authorization prompt is expected for the legacy recognizer.
        let auth = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { @Sendable status in continuation.resume(returning: status) }
        }
        add("speech-auth", "SFSpeechRecognizer.requestAuthorization", "语音权限", "权限结果", "只识别固定样本，不使用麦克风。", String(auth.rawValue), sent: true)
        if auth == .authorized {
            await attempt("legacy-asr", "SFSpeechRecognizer(on-device)", "旧版语音识别") {
                try await self.recognizeFixture(fixture)
            }
        } else {
            add("legacy-asr", "SFSpeechRecognizer(on-device)", "旧版语音识别", "权限阻断", "没有获得语音识别授权。")
        }
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .spokenAudio, options: [.mixWithOthers]); try session.setActive(true)
            defer { try? session.setActive(false, options: .notifyOthersOnDeactivation) }
            let voices = AVSpeechSynthesisVoice.speechVoices().filter { $0.language == "zh-CN" }
            for voice in voices.filter({ $0.identifier.contains("Tingting") || $0.identifier.contains("siri_") }).prefix(3) {
                await attempt("tts-" + voice.identifier, "AVSpeechSynthesizer.write", "语音合成", seconds: 25) {
                    let url = try Self.documents().appendingPathComponent("tts-retest.caf")
                    let info = try await self.synthesize(url: url, voice: voice)
                    return "voice=\(voice.identifier); frames=\(info.frames); sampleRate=\(info.rate)"
                }
            }
        } catch { add("audio-session", "AVAudioSession", "音频会话", "执行失败", error.localizedDescription) }
        let availability = await LanguageAvailability().status(from: Locale.Language(identifier: "en"), to: Locale.Language(identifier: "zh-Hans"))
        add("translation-status", "LanguageAvailability", "翻译", "资源状态", "实际翻译会另外请求。", String(describing: availability))
        await attempt("translation-direct", "TranslationSession(installedSource:target:)", "翻译") {
            let session = TranslationSession(installedSource: Locale.Language(identifier: "en"), target: Locale.Language(identifier: "zh-Hans"))
            return try await session.translate("The garden is quiet after the rain.").targetText
        }
        // Do not call INPreferences without a verified Siri entitlement: Objective-C exceptions are not catchable here.
        add("sirikit", "INPreferences", "旧版 SiriKit", "未调用", "签名未配置 Siri entitlement；保留旧负例，未在本轮重复触发异常。")
        add("siri-voice", "Siri → App Shortcut", "Siri 操作", "等待界面验证", "本轮不直调 ConnectivityIntent，避免把代码调用和 Siri 调用混为一谈。")
    }

    func recognizeFixture(_ url: URL) async throws -> String {
        let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))!
        let request = SFSpeechURLRecognitionRequest(url: url)
        request.requiresOnDeviceRecognition = true
        request.shouldReportPartialResults = false
        return try await withCheckedThrowingContinuation { continuation in
            let sink = RecognitionSink(continuation)
            let task = recognizer.recognitionTask(with: request) { @Sendable result, error in
                if let result, result.isFinal { sink.complete(.success(result.bestTranscription.formattedString)) }
                else if let error { sink.complete(.failure(error)) }
            }
            Task { @MainActor in
                try? await Task.sleep(for: .seconds(30))
                if sink.complete(.failure(ProbeError.timeout)) { task.cancel() }
            }
        }
    }
}

// Speech callbacks arrive on a system queue; serialize the continuation's single completion.
final class RecognitionSink: @unchecked Sendable {
    private let lock = NSLock()
    private var continuation: CheckedContinuation<String, Error>?
    init(_ continuation: CheckedContinuation<String, Error>) { self.continuation = continuation }
    @discardableResult func complete(_ result: Result<String, Error>) -> Bool {
        lock.lock(); let value = continuation; continuation = nil; lock.unlock()
        guard let value else { return false }
        value.resume(with: result); return true
    }
}

@MainActor final class PlaybackProbe: NSObject, AVSpeechSynthesizerDelegate {
    private let synthesizer = AVSpeechSynthesizer()
    private var continuation: CheckedContinuation<String, Error>?
    private var started = false
    func play() async throws -> String {
        synthesizer.delegate = self
        return try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            let utterance = AVSpeechUtterance(string: "你好，这是中文语音接口测试。")
            utterance.voice = AVSpeechSynthesisVoice(language: "zh-CN")
            synthesizer.speak(utterance)
            Task { @MainActor in
                try? await Task.sleep(for: .seconds(20))
                guard let pending = self.continuation else { return }
                self.continuation = nil
                self.synthesizer.stopSpeaking(at: .immediate)
                pending.resume(throwing: ProbeModel.ProbeError.timeout)
            }
        }
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        Task { @MainActor in self.started = true }
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in
            let pending = self.continuation; self.continuation = nil
            pending?.resume(returning: "completed=true; didStart=\(self.started)")
        }
    }
}

extension ProbeModel {
    func runPlaybackAndSiriKit() async {
        guard !running else { return }; running = true; results = []
        defer { running = false; current = "播放与 SiriKit 补测完成"; save() }
        if ProcessInfo.processInfo.arguments.contains("--siri-entitlement-verified") {
            add("sirikit-authorized-query", "INPreferences.siriAuthorizationStatus", "SiriKit", "查询成功", "仅在主机已核验签名有 Siri entitlement 时执行。", String(INPreferences.siriAuthorizationStatus().rawValue), sent: true)
        } else { add("sirikit-authorized-query", "INPreferences", "SiriKit", "签名前置检查未确认", "本轮没有传入主机权限已核验标记。") }
        await attempt("tts-speak", "AVSpeechSynthesizer.speak", "语音播放", seconds: 25) {
            let audio = AVAudioSession.sharedInstance()
            try audio.setCategory(.playback, mode: .spokenAudio, options: [.mixWithOthers]); try audio.setActive(true)
            defer { try? audio.setActive(false, options: .notifyOthersOnDeactivation) }
            return try await PlaybackProbe().play()
        }
    }
}
