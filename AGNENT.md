# Emby 授权测试链条还原手册

> 按用户指定文件名保存为 AGNENT.md；不是自动加载的 AGENTS.md。用途仅限已获授权的安全测试。本文已整合原 apk.txt、caddy.txt（已移除）及当前实现，实际行为以仓库脚本、workflow 和本文的有效 Caddy 配置为准。

## 1. 链条与当前状态

原始客户端请求 mb3admin.com → 解包并替换 smali 中的独立域名 → 重构建、对齐、固定测试签名 → 测试设备向配置域名发起请求 → Caddy 返回预设授权 JSON → 检查客户端是否接受响应。

截至 2026-10-09：

- Caddy 已部署于 5.253.17.117，SSH root、端口 5522；测试域名 emby.nasa.us.ci。
- 三个接口 GET/POST/OPTIONS 共 9 项响应正文对照通过，兜底 404 和原 Grafana 站点检查通过。
- TV、手机 ARM64 Actions 与固定签名已在运行 37896378202 完成完整构建，两项成功；设备端效果未验证。
- 访问隔离尚未配置，当前测试接口公开；后续必须安排隔离与撤销。没有令牌或访问来源限制。
- 已初始化 Git，并配置远程 akvsdk/emby-auto-test；实际构建状态以 Actions 运行记录为准。
- cf-worker/ 是未完成的本地备选实现，本次不提交，不属于当前 Caddy 主链条。

## 2. 文件定位

| 文件 | 用途 |
|---|---|
| 本文第 3 节 | 完整服务端配置；需要时生成文件，不单独提交部署配置 |
| .github/workflows/android-tv-test.yml | 一次手动运行构建 TV、手机两项 job |
| scripts/setup_android_tools.sh | 安装固定 apktool、SDK 工具预检 |
| scripts/prepare_tv.py | 两种客户端的来源选择、版本/ABI 检查、域名替换、构建 |
| scripts/verify_test_certificate.py | 签名证书 SHA-256 校验 |
| scripts/test_prepare_tv.py | 来源选择、域名和替换逻辑单元测试 |
| test-signing/ | 固定公开测试私钥、证书及指纹 |
| ACTION.md | Actions 简明使用说明 |
| AGNENT.md | 原始笔记已归并至此；还原时配合上述可执行文件 |

## 3. 服务端快速还原

### 前置条件

服务器已安装 Caddy 并使用 /etc/caddy/Caddyfile；域名正确解析或代理回源到该服务器，防火墙允许 80/443，HTTPS 证书挑战能完成。有 Cloudflare 管理权限不代表 DNS 记录已创建；当前直连解析已在部署时确认。若开启 Cloudflare 代理，应另行检查回源 TLS、缓存和访问规则。

将下方“有效配置全文”复制为临时 emby-test.Caddyfile，再连接及传送；该临时文件不要提交仓库。也可以让代理直接依据本节生成配置。

本机 PowerShell 连接及传送配置：

~~~powershell
ssh -p 5522 root@5.253.17.117
scp -P 5522 emby-test.Caddyfile root@5.253.17.117:/etc/caddy/emby-test.Caddyfile
~~~

不要直接替换现有主配置，原服务器还有 gr.jjvm.eu.org 的 Grafana 站点。只在主 Caddyfile 顶层加入一次：

~~~caddyfile
import /etc/caddy/emby-test.Caddyfile
~~~

原部署备份为 /etc/caddy/Caddyfile.before-emby。重新操作时先做新的唯一时间戳备份，勿覆盖历史备份。当前 import 已存在，不要重复追加。改域名时只修改新站点主机名，同时配置 DNS，并让 Actions domain 与之相同。

SSH 登录后验证并无中断加载：

~~~sh
/usr/bin/caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
# 只有 validate 成功后才能执行
systemctl reload caddy
systemctl is-active caddy
journalctl -u caddy -n 50 --no-pager
~~~

### 有效配置全文

~~~caddyfile
emby.nasa.us.ci {
    header Content-Type application/json
    @auth path /admin/service/registration/validateDevice /admin/service/registration/validate /admin/service/registration/getStatus
    header @auth {
        Access-Control-Allow-Origin "*"
        Access-Control-Allow-Headers "*"
        Access-Control-Allow-Methods "*"
        Access-Control-Allow-Credentials "true"
    }
    handle /admin/service/registration/validateDevice {
        respond `{"cacheExpirationDays":3650,"isLicensed":true,"licenceStatus":"Licensed","message":"Device Valid","resultCode":"GOOD"}` 200
    }
    handle /admin/service/registration/validate {
        respond `{"featId":"","isLicensed":true,"licenceStatus":"Licensed","registered":true,"expDate":"2099-01-01","key":""}` 200
    }
    handle /admin/service/registration/getStatus {
        respond `{"deviceRecordCount":9999,"registeredUsersCount":9999,"isLicensed":true,"licenceStatus":"Licensed","isTrial":false,"deviceStatus":"","planType":"Lifetime","subscriptions":{}}` 200
    }
    handle {
        respond `{"error":"Emby Auth Server Running"}` 404
    }
}
~~~

三个接口状态均为 200，四个 CORS 头如上；匹配路径不限制方法，查询参数不改变匹配，末尾斜杠不会匹配。其他路径返回 404 与指定错误正文。HEAD 不发送正文。这里还原应用层行为，不保证不同平台的自动响应头、TLS 或压缩逐字节相同。

原 caddy.txt 的 fallback 块及 respond 中的 header 子块不作为有效语法使用，改成 handle 兜底；占位邮箱也不照搬。原 CORS 通配符加 credentials 被保留，不意味着浏览器凭据跨域能工作。

### HTTP 验收

~~~sh
curl -i https://emby.nasa.us.ci/admin/service/registration/validateDevice
curl -i https://emby.nasa.us.ci/admin/service/registration/validate
curl -i https://emby.nasa.us.ci/admin/service/registration/getStatus
curl -i -X POST https://emby.nasa.us.ci/admin/service/registration/validate
curl -i -X OPTIONS https://emby.nasa.us.ci/admin/service/registration/validate
curl -i https://emby.nasa.us.ci/unknown
~~~

前五项应为 200，unknown 应为 404。设备测试前先确认 HTTPS 无证书错误，不使用跳过证书校验的结果作为验收依据。

## 4. GitHub Actions 快速还原

把本目录放入有 Actions 权限的测试仓库并推送默认分支，必须包含 .github/、scripts/、test-signing/，不是只上传 workflow。不要提交下载的 APK、decoded/、out/、SDK 或生产凭据。公开密钥许可不等于允许公开测试 APK；按授权约定管理仓库和 artifact 访问权限。

master 分支上的 workflow、scripts/、test-signing/ 修改会自动构建两项 latest。自定义参数时进入 Actions → Authorized Android TV and mobile test build → Run workflow：

| 输入 | 默认 | 规则 |
|---|---|---|
| domain | emby.nasa.us.ci | 纯 DNS 主机名，不带 https、端口或路径 |
| version | latest | TV versionName；留空也为 latest |
| mobile_version | latest | 手机独立 versionName；留空也为 latest |

两个 job 各自执行，fail-fast=false，一边失败不取消另一边，但整体运行会显示失败。TV 与手机版本通常不同，不要把一个版本号强行用于另一客户端。

上游均为 MediaBrowser/Emby.Releases：

- TV：androidtv/app-google-release.apk。
- 手机：android/emby-android-google-arm64-v8a-release.apk。
- 正确 ARM64 名称为 arm64-v8a，不是 arm64-v7a。TV 文件可能是通用包；脚本检查实际 native 库，有库则必须包含 arm64-v8a，无库则不额外要求原生 ABI。

latest 指各自官方路径当前文件，不代表已经扫描全部商店和预发布渠道。按该路径最近提交 SHA 锁定下载来源，报告记录实际 versionName。指定版本逐个核对最近 100 次文件提交，可能慢，找不到或超过 60 分钟即失败，不静默回退。下载、解包、替换、构建任何一步失败都停止。

### 自动配置的环境

Ubuntu 24.04；Temurin Java 17；Python 3.12；setup-android 初始化 SDK；Build Tools 35.0.0；apktool 2.12.1 官方 JAR。JAR 下载校验 SHA-256：

~~~text
66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa
~~~

setup-android 显式只安装 platform-tools，避免默认旧 tools 包无法获取。工具脚本检查 java/keytool/python3/sdkmanager/openssl/curl 和 aapt/zipalign/apksigner。GitHub token 通过 github.token 供 API 查询，无需新增下载凭据。OpenSSL/curl 仍来自 runner 系统环境；Actions 大版本引用、JDK/Python 小版本并未全部锁定，因此不是完全位级可复现环境。

### 构建行为与产物

下载并检查 → apktool d -r → 修改 smali 域名 → apktool b → zipalign -P 16 → 固定密钥签名 → apksigner 验证 → 证书指纹检查 → 对齐检查 → 上传。

只改 smali 中独立的 mb3admin.com，不做原笔记中对所有文件 sed 的盲目替换。零匹配直接失败。资源文件、拼接/加密域名、native 库端点和证书固定尚未自动处理；不能据此声称 APK 所有请求都已重定向。

成功后下载：

- emby-tv-test-<run_id> → emby-tv-test.apk。
- emby-mobile-test-<run_id> → emby-mobile-test.apk。
- 各包附 report.json、signature.txt、alignment.txt、environment.txt；保留 3 天，两项均成功后另行创建正式公开 Release。
- 环境报告已经生成但后续失败时，上传对应 environment-<client>-failure-<run_id>。

report.json 记录客户端、实际版本、请求版本、来源 SHA/URL、ABI、域名、改动文件/次数、原始及测试 APK SHA-256 与预期证书指纹。latest 会变化；复现时保存报告和原始文件哈希，若版本超出查询窗口则需另行扩展来源解析。

## 5. 固定公开测试签名

两种 APK 默认共用 test-signing/public-test.p12，不再每次随机生成。

| 项目 | 值 |
|---|---|
| 格式 | PKCS#12，RSA 2048，SHA256withRSA |
| 别名 | emby-public-test |
| 库/私钥密码 | public-test-only |
| 证书有效期 | 创建时设置 3650 天，以证书实际日期为准 |
| 证书 SHA-256 | 17:B0:32:99:24:AB:FA:0F:D3:57:EE:B1:A3:35:6E:DE:2F:96:CC:09:F0:AA:B2:FC:1A:51:73:69:50:18:C4:F9 |

这是已明确允许公开的测试私钥，任何人都能签名；不得用于生产、签名权限信任、官方身份证明或正式商店发布。不要覆盖或重新生成，否则证书改变，现有测试安装无法按相同签名更新。只保留 PEM 或指纹不能重建原私钥，恢复签名需要备份完整 p12。

本地检查：

~~~sh
keytool -list -v -keystore test-signing/public-test.p12 -storetype PKCS12 -storepass public-test-only -alias emby-public-test
apksigner verify --verbose --print-certs emby-tv-test.apk
~~~

## 6. 本地复现构建（Linux/bash）

更推荐先跑 Actions。手工复现需自己初始化 SDK、Java 17、Python，并安装 apktool 2.12.1 和 Build Tools 35.0.0；不能直接运行依赖 GITHUB_ENV/GITHUB_PATH 的 CI 环境脚本。

~~~sh
export GH_TOKEN='<有权调用 GitHub API 的令牌，不提交到仓库>'
export TARGET_DOMAIN=emby.nasa.us.ci
export CLIENT=tv                  # 手机改为 mobile
export APK_VERSION=latest         # 或该客户端精确 versionName
export AAPT="$ANDROID_HOME/build-tools/35.0.0/aapt"
export PATH="$ANDROID_HOME/build-tools/35.0.0:$PATH"
python3 -m unittest discover -s scripts -p test_prepare_tv.py -v
python3 scripts/prepare_tv.py
zipalign -P 16 -f 4 rebuilt.apk aligned.apk
export TEST_KEY_PASSWORD=public-test-only
apksigner sign --ks test-signing/public-test.p12 --ks-key-alias emby-public-test --ks-pass env:TEST_KEY_PASSWORD --key-pass env:TEST_KEY_PASSWORD --out "out/emby-$CLIENT-test.apk" aligned.apk
apksigner verify --verbose --print-certs "out/emby-$CLIENT-test.apk" > out/signature.txt
python3 scripts/verify_test_certificate.py out/signature.txt
zipalign -c -P 16 -v 4 "out/emby-$CLIENT-test.apk"
~~~

两种客户端分别使用干净工作目录，避免 original.apk、decoded/、out/ 相互覆盖。手动路径的 report.json 在签名之前产生，不自动补最终 APK 哈希；要完整报告请使用 workflow 的签名后报告步骤。

## 7. 安装与端到端验收

1. 保存 APK、报告、运行 ID、设备系统版本和测试记录。
2. 使用授权测试设备并先备份数据；测试 APK 不能覆盖官方签名安装。不要未经确认自动卸载或清数据。
3. 已装相同测试签名版本时可尝试 adb install -r <测试.apk>；仍需满足版本及兼容条件，不保证降级可安装。
4. 检查启动、登录、核心功能、网络请求实际目标及是否调用这三个接口；必要时在授权范围内取 logcat 或受控抓包，避免记录个人数据。
5. 分别记录“服务端返回预设状态”“客户端显示状态”“受限功能实际行为”，不要把 HTTP 200 或界面显示变化当作完整验证通过。
6. 改域名后必须重新构建安装；仅改服务器 DNS 不会更改 APK 内已有字符串。

## 8. 排障与回滚

- HTTPS 失败：检查 DNS、80/443、Caddy 日志和证书，不以 curl -k 绕过作为修复。
- 零域名匹配：停止，检查新版本的 smali/端点实现；不要删除零匹配保护。
- apktool 构建失败：保留日志和工具版本，检查新 APK 兼容性，不绕过错误继续签名。
- ABI/签名错误：检查来源及 APK，不通过强制安装忽略。
- 服务端成功但客户端失败：排查实际请求、证书固定、其他校验、反篡改和响应解析。
- 版本找不到：最近 100 次提交是检索边界，不自动转最新版。

服务器回滚优先删除本次新增 import，保留后续其他站点修改；验证后 reload。只有确认没有后续配置变化时，才可恢复 /etc/caddy/Caddyfile.before-emby，然后 validate/reload。不要直接整份覆盖新配置。配置文件即使保留，只要取消 import 就不再作为主配置加载。

测试结束移除域名路由/入口与临时访问规则，按授权要求清理设备和产物；公开测试私钥无法通过修改密码变成秘密。本文不改变已有服务器配置，也不替代最终访问隔离方案。

## Release 发布

两项构建都成功后，release job 下载各自 artifact，复核 APK SHA-256，先上传完整附件至草稿，再发布正式 Release 并标记 Latest。标签为 build-<run_id>-<run_attempt>，包含两份 APK、分别命名的报告和 SHA256SUMS.txt。首页 README 使用 releases/latest 下载入口。不增加 debuggable 检查；仍使用固定公开测试签名，不是官方签名。公开仓库的 Release 附件公开可下载。
