import XCTest
import SiriEvaluations

final class SiriPreviewTests: XCTestCase {
    @MainActor func testSiriConnectivity() async throws {
        let scenario = SiriScenario {
            UserTurn("用AI接口检测执行接口连通性测试") {
                SiriResponse(.contains("接口连通性测试成功"))
            }
        }
        do {
            let result = try await SiriService.run(scenario: scenario)
            let text = String(reflecting: result.siriTranscript)
            XCTAssertEqual(result.siriTranscript.turns.count, 1)
            XCTAssertTrue(result.siriTranscript.turns.first?.response.value.contains("接口连通性测试成功") == true)
            XCTAssertTrue(result.siriTranscript.turns.flatMap(\.intentInvocations).contains { $0.value.outcome == .succeeded })
            let attachment = XCTAttachment(string: text)
            attachment.name = "Siri AI scripted connectivity result"
            attachment.lifetime = .keepAlways
            add(attachment)
            print("SIRI_PREVIEW_RESULT: \(text)")
        } catch {
            print("SIRI_PREVIEW_ERROR: \(String(reflecting: error))")
            throw error
        }
    }
}
