#!/usr/bin/env bash
set -euo pipefail
: "${RUNNER_TEMP:?}"
: "${GITHUB_PATH:?}"
: "${GITHUB_ENV:?}"
SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
: "${SDK_ROOT:?Android SDK initialization failed}"
command -v java >/dev/null
command -v keytool >/dev/null
command -v python3 >/dev/null
command -v sdkmanager >/dev/null
command -v openssl >/dev/null
command -v curl >/dev/null
sdkmanager 'build-tools;35.0.0'
build_tools="$SDK_ROOT/build-tools/35.0.0"
for tool in aapt zipalign apksigner; do
  test -x "$build_tools/$tool" || { echo "Missing Android tool: $tool" >&2; exit 1; }
done
bin="$RUNNER_TEMP/emby-test-tools"
mkdir -p "$bin" out
jar="$bin/apktool.jar"
curl --fail --location --retry 3 --connect-timeout 20 --max-time 180 \
  'https://github.com/iBotPeaches/Apktool/releases/download/v2.12.1/apktool_2.12.1.jar' -o "$jar"
printf '%s  %s\n' '66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa' "$jar" | sha256sum --check
cat > "$bin/apktool" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
exec java -jar "$(dirname "$0")/apktool.jar" "$@"
SH
chmod +x "$bin/apktool"
# Check the wrapper and the actual pinned version before publishing PATH.
test "$("$bin/apktool" --version)" = '2.12.1'
printf '%s\n' "$bin" "$build_tools" >> "$GITHUB_PATH"
printf 'AAPT=%s/aapt\n' "$build_tools" >> "$GITHUB_ENV"
{
  echo 'Runner: ubuntu-24.04'
  echo 'apktool: 2.12.1 (SHA-256 verified)'
  echo 'Android build-tools: 35.0.0'
  java -version 2>&1
  python3 --version
  sdkmanager --version
  "$build_tools/aapt" version
  "$build_tools/apksigner" version
  openssl version
} > out/environment.txt
cat out/environment.txt
