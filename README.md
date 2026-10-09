# Emby 授权测试构建

自动构建 Android TV 与 Android 手机 ARM64 测试 APK，测试域名可配置。

## 下载

- **[最新 Release](https://github.com/akvsdk/emby-auto-test/releases/latest)**
- **[Android TV APK](https://github.com/akvsdk/emby-auto-test/releases/latest/download/emby-tv-test.apk)**
- **[Android 手机 ARM64 APK](https://github.com/akvsdk/emby-auto-test/releases/latest/download/emby-mobile-test.apk)**
- [SHA-256 校验文件](https://github.com/akvsdk/emby-auto-test/releases/latest/download/SHA256SUMS.txt)

Release 同时附带两种客户端的来源、版本、域名、签名和对齐报告。APK 为官方 release 输入经授权测试修改后重签的产物，不是官方签名发行包。

## 构建

Actions → **Authorized Android TV and mobile test build** → **Run workflow**：

| 参数 | 默认 | 说明 |
|---|---|---|
| domain | emby.nasa.us.ci | 测试域名，不带协议、路径或端口 |
| version | latest | TV 版本；留空使用当前上游文件 |
| mobile_version | latest | 手机版本，独立于 TV |

修改 master 分支上的 workflow、scripts 或 test-signing 也会自动构建。两项都成功后发布正式 Release，标记 Latest；不发布 debug 包，不增加 debuggable 检查。

## 测试签名与安装

两项 APK 使用仓库内固定的**公开测试签名**，不得用于生产发布或可信身份判断。不能覆盖官方签名安装；同包名、相同测试签名且版本条件满足时可更新旧测试包。安装前备份设备数据。

仅用于已获授权的测试。构建成功不代表设备功能或授权响应测试已经通过。

- [完整链条还原手册](AGNENT.md)
- [Actions 使用说明](ACTION.md)
- [公开测试签名说明](test-signing/README.md)

未完成的 cf-worker/ 不包含在当前提交中。
