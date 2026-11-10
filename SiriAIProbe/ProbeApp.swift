import SwiftUI
import FoundationModels
import Speech
import AVFoundation
import ImagePlayground
import Translation
import AppIntents
import UIKit

struct ProbeResult: Codable, Identifiable, Sendable {
    var id: String
    var api: String
    var category: String
    var status: String
    var detail: String
    var raw: String
    var requestSent: Bool = false
    var timestamp = Date().ISO8601Format()
}

struct ProbeReport: Codable {
    var date = Date().ISO8601Format()
    var os: String
    var locale: String
    var results: [ProbeResult]
}

@Generable struct ShortAnswer {
    @Guide(description: "简体中文的一句简短问候") var greeting: String
}

struct ConnectivityIntent: AppIntent {
    static let title: LocalizedStringResource = "接口连通性测试"
    static let description = IntentDescription("仅写入测试时间并返回固定文字，不调用任何大模型。")
    static let openAppWhenRun = true

    @MainActor func perform() async throws -> some IntentResult & ProvidesDialog {
        let url = try ProbeModel.documents().appendingPathComponent("Intent-events.json")
        var events = (try? JSONDecoder().decode([String].self, from: Data(contentsOf: url))) ?? []
        events.append(Date().ISO8601Format())
        try JSONEncoder().encode(events).write(to: url, options: .atomic)
        return .result(dialog: "接口连通性测试成功。这是固定响应，没有调用大模型。")
    }
}

struct ProbeShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(intent: ConnectivityIntent(),
                    phrases: ["用\(.applicationName)执行接口连通性测试", "在\(.applicationName)中执行连通性测试"],
                    shortTitle: "接口连通性测试", systemImageName: "network")
    }
}

@MainActor @Observable final class ProbeModel {
    var results: [ProbeResult] = []
    var running = false
    var current = "等待开始"
    var reportURL: URL?
    private let synth = AVSpeechSynthesizer()
    private var reportName: String {
        ProcessInfo.processInfo.arguments.contains("--audio-fixture") ? "SiriAI-audio-results.json" : "SiriAI-results.json"
    }

    static func documents() throws -> URL {
        try FileManager.default.url(for: .documentDirectory, in: .userDomainMask,
                                    appropriateFor: nil, create: true)
    }

    func add(_ id: String, _ api: String, _ category: String, _ status: String,
             _ detail: String, _ raw: String = "", sent: Bool = false) {
        results.append(ProbeResult(id: id, api: api, category: category, status: status,
                                   detail: detail, raw: raw, requestSent: sent))
        save()
    }

    func save() {
        do {
            let report = ProbeReport(os: UIDevice.current.systemVersion, locale: Locale.current.identifier, results: results)
            let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
            let url = try Self.documents().appendingPathComponent(reportName)
            try encoder.encode(report).write(to: url, options: .atomic)
            reportURL = url
        } catch { current = "保存失败：\(error.localizedDescription)" }
    }

    func runAudioFixture() async {
        guard !running else { return }
        running = true; results = []
        defer { running = false; current = "音频专项测试结束"; save() }
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playback, mode: .spokenAudio, options: [.mixWithOthers])
            try session.setActive(true)
            defer { try? session.setActive(false, options: .notifyOthersOnDeactivation) }
            current = "中文缓冲区合成复测"
            let voices = AVSpeechSynthesisVoice.speechVoices().filter { $0.language.hasPrefix("zh") }
            add("tts-voices", "AVSpeechSynthesisVoice.speechVoices", "语音合成", "能力查询完成",
                "仅列出中文语音资源；不等于每种声音都已实测。", voices.map { "\($0.identifier):\($0.quality.rawValue)" }.joined(separator: "\n"))
            guard let voice = voices.first(where: { $0.language == "zh-CN" && $0.quality == .default }) ?? AVSpeechSynthesisVoice(language: "zh-CN") else { throw ProbeError.noVoice }
            let url = try Self.documents().appendingPathComponent("Synthetic-speech-retry.caf")
            let info = try await synthesize(url: url, voice: voice)
            add("tts-retry", "AVSpeechSynthesizer.write", "语音合成", info.frames > 0 ? "执行成功" : "返回空音频",
                "复测采用活跃的播放音频会话及基础中文声音；仅生成缓冲区，不播放内容。",
                "voice=\(voice.identifier), frames=\(info.frames), sampleRate=\(info.rate)", sent: true)
        } catch {
            add("tts-retry", "AVSpeechSynthesizer.write", "语音合成", "执行失败",
                "配置音频会话后的复测结果：\(error.localizedDescription)", String(reflecting: error), sent: true)
        }
        current = "中文语音转写独立样本"
        do {
            guard let url = Bundle.main.url(forResource: "ASR-fixture", withExtension: "aiff"),
                  let locale = await SpeechTranscriber.supportedLocale(equivalentTo: Locale(identifier: "zh-CN")) else {
                add("asr-fixture", "SpeechAnalyzer + SpeechTranscriber", "语音识别", "未执行", "固定样本或中文地区支持缺失。")
                return
            }
            let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
            let assetStatus = await AssetInventory.status(forModules: [transcriber])
            guard assetStatus == .installed else {
                add("asr-fixture", "SpeechAnalyzer + SpeechTranscriber", "语音识别", "未执行", "所需模型未安装，不自动下载。", String(describing: assetStatus))
                return
            }
            let start = Date()
            let text = try await transcribe(url: url, transcriber: transcriber)
            let expected = "你好这是中文语音接口测试"
            let matched = text.filter { $0.isLetter } == expected
            add("asr-fixture", "SpeechAnalyzer + SpeechTranscriber", "语音识别", text.isEmpty ? "返回空文本" : "执行成功",
                "固定合成语音由 Mac 生成并随 App 打包；识别实际在 iPhone 上执行。不使用麦克风、不上传个人音频。",
                "text=\(text); exactMatchIgnoringPunctuation=\(matched); elapsedSeconds=\(Date().timeIntervalSince(start))", sent: true)
        } catch {
            add("asr-fixture", "SpeechAnalyzer + SpeechTranscriber", "语音识别", "执行失败", error.localizedDescription, String(reflecting: error), sent: true)
        }
    }

    func run() async {
        guard !running else { return }
        running = true; results = []; defer { running = false; current = "本轮测试结束"; save() }
        current = "端侧模型"
        await testSystem("system-default", model: .default)
        await testSystem("system-general", model: SystemLanguageModel(useCase: .general))
        await testSystem("system-tagging", model: SystemLanguageModel(useCase: .contentTagging))
        current = "Private Cloud Compute"
        let pcc = PrivateCloudComputeLanguageModel()
        add("pcc", "PrivateCloudComputeLanguageModel.availability", "大模型", "权限受限",
            "本测试签名未包含 PCC 专用权限；仅查询状态，不发送云端生成。无法独立归因地区限制。",
            String(describing: pcc.availability))
        add("pcc-permission", "com.apple.developer.private-cloud-compute", "签名权限", "未配置",
            "当前普通开发签名不含托管权限；以主机 codesign 导出的签名与 provisioning profile 为证。")

        current = "系统功能与语音"
        add("writing-tools", "UIWritingToolsCoordinator.isWritingToolsAvailable", "系统 AI 界面",
            UIWritingToolsCoordinator.isWritingToolsAvailable ? "可用性为真" : "可用性为假",
            "仅查询系统写作工具 UI 可用性，不等于完成改写或摘要。",
            String(UIWritingToolsCoordinator.isWritingToolsAvailable))
        add("image-playground", "ImagePlaygroundViewController.isAvailable", "系统 AI 界面",
            ImagePlaygroundViewController.isAvailable ? "可用性为真" : "可用性为假",
            "仅查询图乐园界面资格，不生成图片。", String(ImagePlaygroundViewController.isAvailable))
        let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))
        add("legacy-speech", "SFSpeechRecognizer(zh-CN)", "语音识别", "能力查询完成",
            "没有申请语音识别权限，也未启动旧版识别；支持标记不是转写成功证据。",
            "isAvailable=\(recognizer?.isAvailable.description ?? "nil"), supportsOnDeviceRecognition=\(recognizer?.supportsOnDeviceRecognition.description ?? "nil"), authorizationStatus=\(SFSpeechRecognizer.authorizationStatus().rawValue)")
        let supported = await SpeechTranscriber.supportedLocale(equivalentTo: Locale(identifier: "zh-CN"))
        let installed = await SpeechTranscriber.installedLocales
        add("speech-transcriber", "SpeechTranscriber", "语音识别", "能力查询完成",
            "查询硬件、中文等价地区与已安装模型；不自动下载模型。",
            "isAvailable=\(SpeechTranscriber.isAvailable), supportedChinese=\(supported?.identifier ?? "nil"), installedLocales=\(installed.map(\.identifier).joined(separator: ","))")
        let dictationLocale = await DictationTranscriber.supportedLocale(equivalentTo: Locale(identifier: "zh-CN"))
        let dictationInstalled = await DictationTranscriber.installedLocales
        add("dictation-transcriber", "DictationTranscriber", "语音识别", "能力查询完成",
            "查询听写模型中文支持与已安装语言；本项未运行听写。",
            "supportedChinese=\(dictationLocale?.identifier ?? "nil"), installedLocales=\(dictationInstalled.map(\.identifier).joined(separator: ","))")
        add("sirikit", "INPreferences", "旧版 SiriKit", "缺少 Siri 权限",
            "负例实测：未配置 com.apple.developer.siri 时调用触发系统异常。此为签名要求，不是地区错误；本轮跳过该调用。",
            "NSInternalInconsistencyException: requires the entitlement com.apple.developer.siri")
        let translation = await LanguageAvailability().status(from: Locale.Language(identifier: "en"), to: Locale.Language(identifier: "zh-Hans"))
        add("translation", "LanguageAvailability.status(en→zh-Hans)", "翻译", "能力查询完成",
            "仅查询翻译资源状态，不等于翻译请求成功，也不是 Siri 模型接口。", String(describing: translation))
        do {
            current = "中文语音合成"
            let url = try Self.documents().appendingPathComponent("Synthetic-speech-zh.caf")
            let voice = AVSpeechSynthesisVoice(language: "zh-CN")
            guard let voice else { throw ProbeError.noVoice }
            let info = try await synthesize(url: url, voice: voice)
            add("tts", "AVSpeechSynthesizer.write", "语音合成", info.frames > 0 ? "执行成功" : "返回空音频",
                "固定句子：你好，这是中文语音接口测试。写入音频缓冲区与文件，没有使用麦克风。",
                "voice=\(voice.identifier), frames=\(info.frames), sampleRate=\(info.rate), duration=\(Double(info.frames) / max(info.rate, 1))", sent: true)
            if let supported, SpeechTranscriber.isAvailable {
                let transcriber = SpeechTranscriber(locale: supported, preset: .transcription)
                let assetStatus = await AssetInventory.status(forModules: [transcriber])
                if assetStatus == .installed {
                    current = "本地中文语音转写"
                    let text = try await transcribe(url: url, transcriber: transcriber)
                    add("speech-transcription", "SpeechAnalyzer + SpeechTranscriber", "语音识别",
                        text.isEmpty ? "返回空文本" : "执行成功", "仅转写刚生成的固定合成音频。", text, sent: true)
                } else {
                    add("speech-transcription", "SpeechAnalyzer + SpeechTranscriber", "语音识别", "未执行",
                        "中文语音模型未安装完成，没有自动下载。", String(describing: assetStatus))
                }
            } else {
                add("speech-transcription", "SpeechAnalyzer + SpeechTranscriber", "语音识别", "未执行", "中文模型或设备支持条件未满足。")
            }
        } catch {
            add("speech-execution-error", "TTS / SpeechAnalyzer", "语音执行", "执行失败", error.localizedDescription, String(reflecting: error), sent: true)
        }
        current = "App Intents"
        do {
            _ = try await ConnectivityIntent().perform()
            add("intent-handler", "ConnectivityIntent.perform()", "Siri 操作入口", "代码直调成功",
                "直接调用 AppIntent 处理函数并写入事件。不能据此认定 Siri 语音或快捷指令执行成功。", "Intent-events.json 已新增基线事件", sent: true)
        } catch {
            add("intent-handler", "ConnectivityIntent.perform()", "Siri 操作入口", "执行失败", error.localizedDescription)
        }
        add("siri-voice", "Siri → App Shortcut → AppIntent", "Siri 操作入口", "待人工触发",
            "请对 Siri 说：用AI接口检测执行接口连通性测试。需结合 Siri 响应与新增事件确认，不把代码直调当作语音验收。")
    }

    private func testSystem(_ id: String, model: SystemLanguageModel) async {
        let available = model.isAvailable
        let caps = model.capabilities
        let raw = "availability=\(model.availability); zh-Hans-CN=\(model.supportsLocale(Locale(identifier: "zh-Hans-CN"))); en-US=\(model.supportsLocale(Locale(identifier: "en-US"))); guidedGeneration=\(caps.contains(.guidedGeneration)); toolCalling=\(caps.contains(.toolCalling)); vision=\(caps.contains(.vision)); reasoning=\(caps.contains(.reasoning))"
        add(id, id == "system-tagging" ? "SystemLanguageModel(useCase: .contentTagging)" : id == "system-general" ? "SystemLanguageModel(useCase: .general)" : "SystemLanguageModel.default", "大模型",
            available ? "资格通过" : "资格不通过", "能力标记仅表示模型声明，不能替代真实请求。", raw)
        guard available else {
            add(id + "-generate", "respond / streamResponse / @Generable / Tool", "模型调用方式", "前置阻断",
                "这些是同一模型的调用方式，不是四个独立模型；可用性检查未通过，均未发送生成。")
            return
        }
        do {
            let prompt = id == "system-tagging" ? "为这句话提取两个标签：今天在公园看见了盛开的花。" : "请用简体中文写一句简短问候。"
            let response = try await LanguageModelSession(model: model).respond(to: prompt, options: GenerationOptions(maximumResponseTokens: 120))
            add(id + "-text", "LanguageModelSession.respond", "模型调用方式", "执行成功", "真实文本请求。", response.content, sent: true)
            if id != "system-tagging", caps.contains(.guidedGeneration) {
                let structured = try await LanguageModelSession(model: model).respond(to: "用简体中文问好。", generating: ShortAnswer.self, options: GenerationOptions(maximumResponseTokens: 120))
                add(id + "-structured", "respond(generating:)", "模型调用方式", "执行成功", "真实结构化请求。", structured.content.greeting, sent: true)
            }
        } catch {
            add(id + "-error", "LanguageModelSession.respond", "模型调用方式", "执行失败", error.localizedDescription, String(reflecting: error), sent: true)
        }
    }

    private func transcribe(url: URL, transcriber: SpeechTranscriber) async throws -> String {
        let analyzer = SpeechAnalyzer(modules: [transcriber])
        let timeout = Task {
            do { try await Task.sleep(for: .seconds(25)); await analyzer.cancelAndFinishNow() }
            catch { }
        }
        defer { timeout.cancel() }
        let collect = Task {
            var parts: [String] = []
            for try await result in transcriber.results { parts.append(String(result.text.characters)) }
            return parts.joined()
        }
        do {
            try await analyzer.start(inputAudioFile: AVAudioFile(forReading: url), finishAfterFile: true)
            return try await collect.value
        } catch {
            collect.cancel(); await analyzer.cancelAndFinishNow(); throw error
        }
    }

    private func synthesize(url: URL, voice: AVSpeechSynthesisVoice) async throws -> AudioInfo {
        let sink = AudioSink(url: url)
        return try await withCheckedThrowingContinuation { continuation in
            sink.continuation = continuation
            let utterance = AVSpeechUtterance(string: "你好，这是中文语音接口测试。")
            utterance.voice = voice
            synth.write(utterance) { buffer in sink.consume(buffer) }
            Task { @MainActor in
                try? await Task.sleep(for: .seconds(20))
                if sink.failIfPending() { synth.stopSpeaking(at: .immediate) }
            }
        }
    }

    enum ProbeError: LocalizedError {
        case noVoice, timeout
        var errorDescription: String? { self == .noVoice ? "没有中文语音" : "音频生成超时" }
    }
}

struct AudioInfo: Sendable { let frames: Int64; let rate: Double }

// 音频回调由系统线程调用；锁保护文件、累计值与 continuation 的单次完成。
final class AudioSink: @unchecked Sendable {
    let url: URL
    let lock = NSLock()
    var file: AVAudioFile?
    var frames: Int64 = 0
    var rate: Double = 0
    var continuation: CheckedContinuation<AudioInfo, Error>?
    init(url: URL) { self.url = url }
    func consume(_ buffer: AVAudioBuffer) {
        lock.lock(); defer { lock.unlock() }
        guard let continuation, let pcm = buffer as? AVAudioPCMBuffer else { return }
        do {
            if pcm.frameLength == 0 {
                self.continuation = nil; file = nil
                continuation.resume(returning: AudioInfo(frames: frames, rate: rate)); return
            }
            if file == nil { file = try AVAudioFile(forWriting: url, settings: pcm.format.settings) }
            try file?.write(from: pcm); frames += Int64(pcm.frameLength); rate = pcm.format.sampleRate
        } catch {
            self.continuation = nil; file = nil; continuation.resume(throwing: error)
        }
    }
    func failIfPending() -> Bool {
        lock.lock(); defer { lock.unlock() }
        guard let continuation else { return false }
        self.continuation = nil; file = nil
        continuation.resume(throwing: ProbeModel.ProbeError.timeout); return true
    }
}

@main struct ProbeApp: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

struct ProbeView: View {
    @State private var model = ProbeModel()
    @State private var sampleText = "今天我们完成了一次系统接口检查。接下来会核对每项结果，并把需要继续验证的功能整理成清单。"
    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("独立测试系统模型与 Siri 公开入口，不读取个人数据，不使用麦克风。")
                    Text(model.current).foregroundStyle(.secondary)
                    Button(model.running ? "测试进行中…" : "重新运行检查") { Task { await model.run() } }.disabled(model.running)
                    if let url = model.reportURL { ShareLink("导出原始 JSON 报告", item: url) }
                }
                Section("Siri 连通性人工测试") {
                    Text("对 Siri 说：用AI接口检测执行接口连通性测试。成功响应应说明这是固定响应，没有调用大模型。")
                    SiriTipView(intent: ConnectivityIntent())
                }
                Section("写作工具人工测试") {
                    Text("长按下方文字并全选，检查是否有写作工具，再尝试润色或摘要。")
                    TextEditor(text: $sampleText).frame(minHeight: 130).writingToolsBehavior(.complete)
                }
                ForEach(model.results) { result in
                    Section(result.api) {
                        Text(result.status).font(.headline)
                        Text(result.detail).font(.callout)
                        if !result.raw.isEmpty { Text(result.raw).font(.caption.monospaced()).textSelection(.enabled) }
                    }
                }
            }
            .navigationTitle("Siri AI 接口检测")
            .task {
                if model.results.isEmpty {
                    if ProcessInfo.processInfo.arguments.contains("--audio-fixture") { await model.runAudioFixture() }
                    else { await model.run() }
                }
            }
        }
    }
}
