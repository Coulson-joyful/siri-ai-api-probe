# Siri AI API Probe

独立检查 Siri / Apple Intelligence 公开接口的 SwiftUI 真机工具，并附 2026-11-10 的脱敏测试报告。

- [HTML 测试报告](report.html)：下载后用浏览器打开，支持搜索、筛选和打印。
- [测试结论矩阵](Evidence/Test-summary.json)
- [Apple 官方来源](Evidence/Official-sources.json)
- [脱敏说明](PRIVACY.md)

> 本次国行 iPhone 16 Pro / iOS 27.3 的局部结果，不能外推为所有中国大陆设备的统一可用性。

## 工具说明

这是独立于业务 App 的接口检测工程。只使用固定测试文字和合成音频，不读取个人内容，不使用麦克风，不修改系统地区或账号设置。

## 覆盖范围

- `SystemLanguageModel.default`、`.general`、`.contentTagging`：资格、中文/英文支持、声明能力；资格通过才发起文本与结构化生成。
- `PrivateCloudComputeLanguageModel`：读取可用性。当前签名未包含 `com.apple.developer.private-cloud-compute`，不发送云端请求。
- 写作工具和图乐园：查询系统 UI 可用性；写作工具还提供固定样本文本，方便人工验证。
- `SFSpeechRecognizer`、`SpeechTranscriber`、`DictationTranscriber`：支持和资源状态；新语音转写另有真实固定音频测试。
- `AVSpeechSynthesizer.write`：真实中文缓冲区合成，包括配置音频会话后的专项复测。
- Translation：仅查询英语到简体中文的资源状态，不运行翻译。
- `AppIntent.perform()`：直调连通性函数并写入基线事件。另声明 `AppShortcut`，供用户通过 Siri 人工触发。

`requestSent` 表示该检测项是否实际执行请求／处理函数，不表示有网络请求，也不表示执行成功。大模型资格被阻断的记录均为 false。

## 运行

使用 Xcode 27.2 或更新版本打开 `SiriAIProbe.xcodeproj`，选择自己的开发团队和唯一 Bundle ID，连接并解锁设备后运行。工程默认不设置团队、不嵌入证书、不添加 PCC 或 SiriKit 专用权限。

正常启动自动运行接口矩阵并写入 `Documents/SiriAI-results.json`。Siri 的每次 `ConnectivityIntent.perform()` 调用会在 `Documents/Intent-events.json` 新增时间。直接调用、快捷指令调用和 Siri 调用使用同一处理函数，因此事件本身不能识别入口来源；须结合操作记录确认。

在启动参数加入 `--audio-fixture`，单独执行音频复测并写入 `Documents/SiriAI-audio-results.json`。其中文语音样本由 macOS Tingting 声音生成，固定内容为“你好，这是中文语音接口测试。”，随 App 打包；识别运行于目标 iPhone。没有下载新语音模型。

## 特别注意

1. 旧版 `INPreferences` 在没有 `com.apple.developer.siri` 权限时会抛 Objective-C 异常，Swift 的普通 `do/catch` 无法捕获。已记录负例，最终检测工程跳过该危险调用。这个权限要求不能解释为地区限制。
2. 本机 SDK 为 27.2，实际编译检查显示没有 `SiriEvaluations` 模块，也没有 `@AppIntent(.tool)` 新签名。27.3 开发者预览的新功能必须用匹配 SDK 再测试；当前标准 App Shortcut 不能代替新预览端到端验收。
3. PCC 是托管权限，需满足 Apple 开发者资格与分发条件；不能通过手工在 entitlements 文件中添加 true 来取得资格。
4. `supportsLocale`、`capabilities`、`isAvailable`、已安装语言均不能当作成功推理或成功转写证据。
5. 本机测试无法独立归因地区：未切换账号、地区或系统，也没有非大陆对照设备。报告分别列示官方限制与本次观察。

本次实际结果与官方来源见同目录 `Evidence` 和 [HTML 报告](report.html)。

## 本次人工验证与报告检查

用户反馈：Siri 返回预期固定响应；写作工具操作成功。匿名验证摘要保存在 Evidence/Manual-tests.json。Siri 连通性事件文件无法独立区分入口，人工反馈是路由成功结论的关键证据。

HTML 已做结构、锚点、证据一致性和脚本语法检查；内置浏览器不允许自动打开 file URL，未完成浏览器视觉验收。
