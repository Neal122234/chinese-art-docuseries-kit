#!/usr/bin/env bash
# 提交 / 推送前扫一遍仓库里有没有密钥、Token、cookie、凭据文件路径。
# 用法：scripts/check_secrets.sh [目录，缺省仓库根]；有命中退出码 1，逐条列出 文件:行号:片段。
# 命中不一定是泄露（比如文档里讲"cookie 校验"），逐条看过再决定；真密钥要删掉并去对应平台作废重发。
set -uo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="${1:-$KIT}"
SELF="scripts/check_secrets.sh"
EXCL=(--exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=__pycache__
      --exclude-dir=cache --exclude="$(basename "$SELF")" --exclude=.gitignore)

# 名称 | 扩展正则（grep -E，大小写敏感的放前面，-i 的单独一组）
PATTERNS=(
  'AWS access key|AKIA[0-9A-Z]{16}'
  'GitHub token|(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}'
  'OpenAI/Anthropic key|sk-(ant-|proj-)?[A-Za-z0-9_-]{20,}'
  'Google API key|AIza[0-9A-Za-z_-]{35}'
  'Slack token|xox[abprs]-[A-Za-z0-9-]{10,}'
  'HuggingFace token|hf_[A-Za-z0-9]{30,}'
  'Tavily key|tvly-[A-Za-z0-9_-]{16,}'
  'Private key block|-----BEGIN ([A-Z]+ )?PRIVATE KEY-----'
  'JWT|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}'
  'Bilibili cookie|SESSDATA|bili_jct|DedeUserID__ckMd5'
  'Douyin/XHS/Kuaishou cookie|sessionid_ss|sid_tt|passport_csrf_token|msToken|web_session|kuaishou\.server\.web_st'
)
PATTERNS_I=(
  'Generic secret assignment|(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'[:space:]]{8,}'
  'Cookie header/value|(^|[^a-z])cookies?["'"'"']?[[:space:]]*[:=]|set-cookie|--cookies?([[:space:]]|=)'
  'Bearer token|bearer[[:space:]]+[A-Za-z0-9._~+/-]{20,}'
  'Credential paths|~/\.config|/\.config/|\.netrc|\.aws/credentials|\.ssh/id_|cookies?\.(json|txt)|keychain'
)

hits=0
scan() {  # $1 名称  $2 正则  $3 额外 grep 选项
  local name="$1" re="$2" opt="${3:-}" out
  out=$(grep -rInE $opt "${EXCL[@]}" -e "$re" "$ROOT" 2>/dev/null | cut -c1-220)
  if [[ -n "$out" ]]; then
    echo "## $name"; echo "$out" | sed "s|^$ROOT/||"; echo
    hits=$((hits + $(echo "$out" | wc -l)))
  fi
}
for p in "${PATTERNS[@]}";   do scan "${p%%|*}" "${p#*|}"; done
for p in "${PATTERNS_I[@]}"; do scan "${p%%|*}" "${p#*|}" -i; done

# 凭据类文件名
files=$(find "$ROOT" \( -name .git -o -name .venv -o -name node_modules \) -prune -o -type f \
  \( -name '.env' -o -name '.env.*' -o -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name 'id_rsa*' \
     -o -iname '*cookie*' -o -name '.netrc' -o -name 'credentials*' \) -print 2>/dev/null)
if [[ -n "$files" ]]; then echo "## 凭据类文件名"; echo "$files" | sed "s|^$ROOT/||"; echo; hits=$((hits + $(echo "$files" | wc -l))); fi

if [[ $hits -eq 0 ]]; then echo "check_secrets: 0 命中（${ROOT}）"; exit 0; fi
echo "check_secrets: $hits 处命中，逐条确认"; exit 1
