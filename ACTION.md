# Android TV 与手机 ARM64 授权测试流水线

将目录推送到测试 GitHub 仓库默认分支；当前仓库为公开仓库，日志与产物按公开处理，不包含生产凭据或个人数据。在 Actions → Authorized Android TV and mobile test build → Run workflow 中配置：

- domain：测试主机名，默认 emby.nasa.us.ci；不带协议、路径或端口。
- version：TV 版本，留空/latest 使用官方 androidtv/app-google-release.apk 当前文件。
- mobile_version：手机版本，留空/latest 使用官方 android/emby-android-google-arm64-v8a-release.apk 当前文件。

两项版本参数独立，指定版本须与各自 APK versionName 精确匹配。一次运行默认启动 tv、mobile 两个隔离 job，任一失败不会取消另一项，但整体运行仍会标记失败。产物分别为 emby-tv-test-<run_id> 和 emby-mobile-test-<run_id>，内含 emby-tv-test.apk 或 emby-mobile-test.apk 及各自报告。

当前官方 TV 目录提供 Google 和 Amazon 两种包，TV job 选择 Google TV 包，mobile job 选择普通 Android Google ARM64 包。下载后检查原生库 ABI；无原生库不额外限制 ARM 架构，有原生库则要求包含 arm64-v8a。

指定版本检索最近 100 次各自文件提交，逐个下载核对，可能较慢；找不到或超时直接失败。这不是无限历史版本库。latest 指各自官方路径当前文件，不声称覆盖其他发布渠道。

只替换解包 smali 中独立的 mb3admin.com 主机名；无匹配则停止。混淆、拼接域名、资源中的端点或证书固定需要另行分析，构建成功不保证客户端验证成功。

TV 与手机共用 test-signing/public-test.p12 中的固定公开测试密钥，密码和私钥均允许公开；不得用于生产或信任判定。签名后检查证书 SHA-256。测试 APK 不能覆盖官方安装；同包名、相同测试签名且版本条件满足时可跨运行更新，安装前应备份测试设备数据。产物保存 3 天，包含 APK、来源/版本/域名/文件修改报告、哈希、签名及对齐验证结果，不发布公共 Release。

当前仅做了本地脚本单元测试，尚未在 GitHub runner 上构建。通过 setup-android 显式初始化 SDK；Java 17、Python 3.12 显式配置；apktool 固定 2.12.1 并校验硬编码 SHA-256，SDK build-tools 固定 35.0.0。环境预检输出保存在 environment.txt。涉及资源/反篡改兼容问题时应停止并检查，不跳过失败。

仅用于获准的隔离测试；上线前完成测试接口访问隔离。本 workflow 不修改服务器或 Cloudflare 配置。
