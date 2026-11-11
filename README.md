# Siri AI API Probe

独立检查 Siri／Apple Intelligence 公开接口的 SwiftUI 真机工具，报告按三类呈现：用户可直接使用的功能、开发者可以调用的模型／参数／函数，以及中国大陆的官方开放限制。每项保留 2026-11-11 的实测结果和未完成项。最新使用 **Xcode 27.3 beta（27C5020n）／iOS 27.3 SDK**；最低部署版本为 iOS 27.3。

- [HTML 报告](report.html)：下载后可离线阅读，支持用途搜索、结果筛选和打印。
- [最新脱敏证据](Evidence/2026-11-11/)
- [历史 2026-11-10 证据](Evidence/)
- [官方来源](Evidence/Official-sources.json)
- [脱敏说明](PRIVACY.md)

## 当前主要结果

| 接口 | 用途 | 结果 |
|---|---|---|
| SystemLanguageModel：default／general／contentTagging | 通用文本生成、理解、分类标签 | 均为 deviceNotEligible，未生成 |
| PCC／三个推理档位 | 云端长文与复杂推理 | 资格阻断，签名还缺 PCC 托管权限 |
| SpeechTranscriber | 固定音频转文字 | 成功，内容符合样本 |
| DictationTranscriber／旧版端侧识别 | 听写、兼容语音输入 | 有输出，但“这是”被识别为“就是” |
| AVSpeechSynthesizer.speak | 中文朗读播放 | 收到开始、完成回调；约 5 秒 |
| AVSpeechSynthesizer.write | 生成音频文件／缓冲区 | 三种中文声音均超时 |
| 翻译系统 UI | 用户准备资源后翻译 | 27.3 SDK 构建再次取得中文输出 |
| 翻译直接初始化 | 已安装语言的无界面翻译 | 27.3 SDK 实际请求仍返回 notInstalled |
| Image Playground | 系统图片生成界面 | 实际打开提示此 iPhone 不可用 |
| INPreferences | 旧 SiriKit 授权查询 | 有 Siri entitlement 后查询成功；状态 notDetermined |
| ToolIntent | 向 Siri AI 暴露自定义动作 | 27.3 SDK 编译、签名、安装通过；未完成自然语言运行验收 |
| SiriEvaluations | 脚本化 Siri 测试 | 模块和 UI 目标构建通过；真机运行器 code 74，未进入场景 |
| 快捷指令四类模型 | 系统“使用模型”工作流 | 动作搜索“模型”为空；没有逐个运行模型请求 |

Siri 标准动作与写作工具的本轮人工结果以 HTML 和最新证据为准。历史成功反馈不能代替本轮实测。支持标记、编译通过、接口执行成功、内容准确性是不同结论。

## 运行

用 Xcode 27.3 或更新版打开 `SiriAIProbe.xcodeproj`，选择自己的开发团队、设置 `PROBE_BUNDLE_ID` 为唯一 Bundle ID，然后在解锁的真机运行。工程默认不嵌入团队、证书或个人账号；普通 Siri entitlement 用于旧 SiriKit 查询，不包含 PCC 托管资格。

```sh
xcodebuild -project SiriAIProbe.xcodeproj -scheme SiriAIProbe \
  -destination 'id=YOUR_DEVICE_ID' \
  DEVELOPMENT_TEAM=YOUR_TEAM PROBE_BUNDLE_ID=YOUR_UNIQUE_BUNDLE_ID \
  -allowProvisioningUpdates build
```

若机器有多个 Xcode，请为命令设置对应 `DEVELOPER_DIR`，不要仅凭全局选择器推断实际 SDK。

- 默认启动或 `--extended`：运行扩展矩阵。请求语音识别授权，必要时尝试下载中文转写资源；只识别固定合成音频，不调用麦克风。输出 `Documents/SiriAI-results.json` 或 `SiriAI-extended-results.json`。
- `--playback-only --siri-entitlement-verified`：普通语音播放与旧 SiriKit 查询。**只有先在主机核验实际签名含 Siri entitlement，才能传入后一个参数**；否则跳过旧 SiriKit 调用。输出 `SiriAI-playback-results.json`。
- `--audio-fixture`：原有音频专项路径，保留兼容；不代表最新完整矩阵。
- `--ui-only`：不自动运行矩阵，用于写作工具、翻译、图乐园及固定样本文字的人工操作。

测试 App 提供“执行英中翻译”按钮，可在系统界面下载所需语言；写作工具的固定文本需要用户手动选择并运行。每次实际连通性 intent 执行会写入 `Documents/Intent-events.json`；事件不能独立区分 Siri、快捷指令或直接函数调用，必须结合操作记录。

`requestSent` 表示实际执行了请求／函数，不表示网络传输或结果正确。`*-start` 是开始进度，不能作为成功结果；应查看同 ID 最终记录。

## 新 Siri 评测

`SiriAIProbeTests` 是 **UI 测试目标**，调用 `SiriEvaluations.SiriService.run`，检查固定连通性回复和成功 intent 调用。此框架不能在普通单元测试目标执行。最新环境中测试目标已编译安装，但运行器在场景开始前连接失败；目前没有评测通过结论，也没有把这个问题归因于中国大陆政策。

```sh
xcodebuild -project SiriAIProbe.xcodeproj -scheme SiriAIProbe \
  -destination 'id=YOUR_DEVICE_ID' \
  DEVELOPMENT_TEAM=YOUR_TEAM PROBE_BUNDLE_ID=YOUR_UNIQUE_BUNDLE_ID \
  -parallel-testing-enabled NO -allowProvisioningUpdates test
```

实体检索、屏幕上下文、跨 App 数据传递、复杂参数与安全确认尚未得到端到端验收；本工具不能将未开放的系统能力变成任意后台模型 API。

## 报告更新与边界

报告共有三类主内容，原始返回值收在可展开的测试记录中。更新 `Evidence/2026-11-11/` 下的脱敏证据后，运行：

```sh
python3 Scripts/render_report.py
```

渲染脚本只读取公开证据，校验行数、列数、锚点与已知个人标识；不会读取原始诊断包。原始崩溃日志、Xcode 运行器诊断包、个人签名配置不应提交。

本次结果仅对应目标设备、系统、语言、资源和签名条件。没有更改账号／地区／语言，没有非大陆对照组，没有得出所有中国大陆设备统一可用性的结论。系统产品功能目录也没有整体逐项验收。
