#!/usr/bin/env bash
# 提交 / 推送前的机械检查（INC-002 / INC-004 / INC-005 的固化）。
#
# 两个模式：
#   提交前：SCOPE_ROLE=assistant tools/precommit_check.sh --scope docs/ tools/ --message "docs: xxx"
#   推送前：EXAMINER_OK="考官 <hash> 可发布" tools/precommit_check.sh --push   # 或手动带 --examiner-ok="..."
#
# 检查项（提交模式）：
#   1. 空提交：暂存区与 HEAD 无差异 → 拒绝
#   2. 提交信息为空 / 太短 / 占位（wip、test、build trigger…）→ 拒绝
#   3. `git add -A` 卷入未声明改动：给了 --scope 时，暂存文件越界 → 拒绝
#   4. 调试残留 / 凭据入暂存（*.log、*.jks、keystore-info*、*.bak）→ 拒绝
#   5. 过期文档文案（A-10）：旧文件数/旧测试数/退役实例名，以及「N 项」「N/N」类
#      写死数字（上下文防误报；豁免 docs/history、docs/audit、docs/generated、
#      docs/org/PLAN-*、B 队卡、docs/HANDOVER、「永久禁用/退役名/旧名」行）→ 拒绝
#   6. 写入范围（A-17）：暂存路径须落在声明的职位写入范围内
#      （SCOPE_ROLE=<职位|实例名> 或 --role；默认警告，--strict 拒绝；缺省警告）
#   7. 工作区还有未提交改动 / 文件被部分暂存 → 警告（可能卷进队友改动）
#
# 检查项（推送模式）：
#   0. 考官门禁复位（A-18）：docs/BATCHES.md 末行含「待复核/待考官」→ 拒绝，
#      除非带 --examiner-ok="<回执摘要>"（或环境变量 EXAMINER_OK）；--no-examiner 跳过
#   1. 远端有本地没有的提交（被 amend/rebase/强推改写过）→ 拒绝
#   2. 待推提交里有空提交或空信息 → 拒绝
#   3. 提示本次推送会不会触发 CI（只有触及 native-emu/** 才会）
#
# 装成本地钩子（只影响本机 .git，不进仓库）：
#   tools/precommit_check.sh --install-hooks
#
# 退出码：0 = 通过（可能带警告），1 = 拦住，2 = 用法错误。
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

MODE="commit"
MESSAGE=""
MESSAGE_FILE=""
SCOPE=()
INSTALL_HOOKS=0
ERRORS=0
WARNINGS=0
STRICT=0
ROLE="${SCOPE_ROLE:-}"
EXAMINER_OK="${EXAMINER_OK:-}"
NO_EXAMINER=0

usage() {
    sed -n '2,42p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
}

ok()   { printf '  ✓ %s\n' "$*"; }
warn() { printf '  ! %s\n' "$*"; WARNINGS=$((WARNINGS + 1)); }
err()  { printf '  ✗ %s\n' "$*"; ERRORS=$((ERRORS + 1)); }

while [ $# -gt 0 ]; do
    case "$1" in
        --push)         MODE="push"; shift ;;
        --message)      MESSAGE="${2:-}"; shift 2 ;;
        --message-file) MESSAGE_FILE="${2:-}"; shift 2 ;;
        --install-hooks) INSTALL_HOOKS=1; shift ;;
        --scope)
            shift
            while [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; do
                SCOPE+=("$1"); shift
            done
            ;;
        --no-scope)     SCOPE=(); shift ;;
        --strict)       STRICT=1; shift ;;
        --role)         ROLE="${2:-}"; shift 2 ;;
        --role=*)       ROLE="${1#*=}"; shift ;;
        --examiner-ok)  EXAMINER_OK="${2:-}"; shift 2 ;;
        --examiner-ok=*) EXAMINER_OK="${1#*=}"; shift ;;
        --no-examiner)  NO_EXAMINER=1; shift ;;
        -h|--help)      usage ;;
        *) echo "未知参数：$1（--help 看用法）" >&2; exit 2 ;;
    esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "不在 git 仓库里" >&2; exit 2; }

# ---------- 装钩子 ----------
install_hooks() {
    local dir hooks
    dir="$(git rev-parse --git-dir)"
    hooks="$dir/hooks"
    mkdir -p "$hooks"
    cat > "$hooks/pre-commit" <<'HOOK'
#!/usr/bin/env bash
ROOT="$(git rev-parse --show-toplevel)"
PRE_COMMIT_HOOK=1 exec "$ROOT/tools/precommit_check.sh" --message-file "${COMMIT_MSG_FILE:-}" "$@"
HOOK
    cat > "$hooks/pre-push" <<'HOOK'
#!/usr/bin/env bash
ROOT="$(git rev-parse --show-toplevel)"
exec "$ROOT/tools/precommit_check.sh" --push
HOOK
    chmod +x "$hooks/pre-commit" "$hooks/pre-push"
    echo "已安装本地钩子：$hooks/pre-commit、$hooks/pre-push"
    echo "注意：钩子只在本机 .git 里，不进仓库，换设备要重装。"
}

if [ "$INSTALL_HOOKS" = "1" ]; then
    install_hooks
    exit 0
fi

# ---------- A-17 写入范围 ----------
# 从 tools/write_scopes.json 取某职位的允许路径（每行一个）；退出码 3=表读取失败，4=无此职位
write_scope_paths() {
    python3 - "$ROOT/tools/write_scopes.json" "$1" <<'PY'
import json, sys
path, role = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(path, encoding="utf-8"))
except Exception:
    sys.exit(3)
roles = d.get("roles", {})
info = roles.get(role)
if info is None:
    for k, v in roles.items():
        if role in (v.get("aliases") or []):
            info = v
            break
if info is None:
    sys.exit(4)
for p in info.get("paths") or []:
    print(p)
PY
}

path_in_patterns() {  # $1=文件；依赖 WRITE_PATTERNS 数组
    local f="$1" p
    for p in "${WRITE_PATTERNS[@]}"; do
        [ "$p" = "*" ] && return 0
        if [[ "$p" == *"*"* ]]; then
            [[ "$f" == $p ]] && return 0
        elif [[ "$p" == */ ]]; then
            [[ "$f" == "$p"* ]] && return 0
        else
            [[ "$f" == "$p" || "$f" == "$p"/* ]] && return 0
        fi
    done
    return 1
}

# ---------- 提交信息检查 ----------
check_message() {  # $1 = 文本，$2 = 来源描述
    local text="$1" label="${2:-提交信息}"
    text="$(printf '%s' "$text" | sed '/^#/d' | sed '/^$/d')"
    if [ -z "$text" ]; then
        err "$label为空"
        return
    fi
    local first
    first="$(printf '%s' "$text" | head -1)"
    if [ "${#first}" -lt 6 ]; then
        err "$label太短（<$first>）：写人话，它会变成 OTA 更新说明"
        return
    fi
    case "$first" in
        wip|WIP|tmp|temp|test|Test|update|fix|修改|更新|临时|草稿|asdf|xxx)
            err "$label是占位词（<$first>）：写清楚做了什么" ;;
        *"build trigger"*|*"触发构建"*)
            err "$label含「触发构建」：禁止用空提交/临时注释触发 CI（INC-002）" ;;
        *)
            ok "$label：$first" ;;
    esac
}

# ---------- 提交模式 ----------
commit_checks() {
    echo "== 提交前检查 =="

    # 1. 空提交
    if git diff --cached --quiet; then
        err "空提交：暂存区与 HEAD 没有差异（禁止用空提交触发构建，INC-002）"
        return
    fi
    ok "暂存区有改动"

    # 暂存文件清单
    local staged=()
    while IFS= read -r f; do
        [ -n "$f" ] && staged+=("$f")
    done < <(git diff --cached --name-only --diff-filter=ACMRD)
    if [ "${#staged[@]}" -eq 0 ]; then
        err "暂存区没有文件（可能只暂存了文件模式变化？）"
    fi

    # 2. 提交信息
    local msg="$MESSAGE"
    if [ -n "$MESSAGE_FILE" ] && [ -f "$MESSAGE_FILE" ]; then
        msg="$(cat "$MESSAGE_FILE")"
    fi
    # 只有经钩子调用时才读 COMMIT_EDITMSG；手动跑时读它会把上一条提交信息当成这次的
    if [ -z "$msg" ] && [ "${PRE_COMMIT_HOOK:-0}" = "1" ]; then
        msg="$(cat "$(git rev-parse --git-dir)/COMMIT_EDITMSG" 2>/dev/null || true)"
    fi
    if [ -z "$msg" ]; then
        err "没给提交信息：用 --message 或 --message-file（钩子方式会自动读 COMMIT_EDITMSG）"
    else
        check_message "$msg"
    fi

    # 3. 写入范围：给了 --scope 就必须全部落在范围内（防 git add -A，INC-004）
    if [ "${#SCOPE[@]}" -gt 0 ]; then
        local f p matched outside=()
        for f in "${staged[@]}"; do
            matched=0
            for p in "${SCOPE[@]}"; do
                # 支持目录前缀（docs/、docs）、glob（docs/*.md）
                if [[ "$p" == *"*"* ]]; then
                    [[ "$f" == $p ]] && { matched=1; break; }
                elif [[ "$p" == */ ]]; then
                    [[ "$f" == "$p"* ]] && { matched=1; break; }
                else
                    [[ "$f" == "$p" || "$f" == "$p"/* ]] && { matched=1; break; }
                fi
            done
            [ "$matched" = "1" ] || outside+=("$f")
        done
        if [ "${#outside[@]}" -gt 0 ]; then
            err "暂存了 ${#outside[@]} 个未声明文件（疑似 git add -A 卷入队友改动，INC-004）："
            printf '      %s\n' "${outside[@]}"
            echo "      本次声明范围：${SCOPE[*]}；如确需提交，补 --scope 或 git restore --staged <文件>"
        else
            ok "暂存文件都在声明范围内（${SCOPE[*]}）"
        fi
    else
        warn "没给 --scope：无法判断是否卷入未声明改动，建议 --scope <路径>"
    fi

    # 4. 调试残留 / 凭据
    local f residue=()
    for f in "${staged[@]}"; do
        case "$f" in
            *.log|*.jks|keystore-info*|*.bak|*.bak.*|*~) residue+=("$f") ;;
        esac
    done
    if [ "${#residue[@]}" -gt 0 ]; then
        err "暂存了调试残留/凭据类文件：${residue[*]}"
    else
        ok "没有调试日志 / 密钥库进暂存"
    fi

    # 5. 过期文档文案（A-10）：旧文件数 / 旧测试数 / 退役实例名 + 写死的「N 项」「N/N」
    #    防误报：文件级豁免下表的目录；「N 项」允许 指标/保留/核对/生命周期 上下文；
    #    「N/N」允许 test_results/run_tests/CI/测试/批次/坐标 等上下文；只兜已知过期值不受上下文限制。
    local stale=() f hit
    local p_exact='57 个|28/28|verifier'
    local p_items='[0-9]+ 项(?!目)'
    local p_ratio='(?<![A-Za-z0-9_])[0-9]+/[0-9]+(?![A-Za-z0-9_])'
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        while IFS= read -r hit; do
            [ -n "$hit" ] && stale+=("$hit")
        done < <( { grep -nP "$p_exact" "$f" 2>/dev/null | grep -vE '永久禁用|退役名|旧名'
                    grep -nP "$p_items" "$f" 2>/dev/null | grep -vE '指标|METRICS|保留|核对|生命周期'
                    grep -nP "$p_ratio" "$f" 2>/dev/null | grep -vE 'test_results|run_tests|CI |CI run|首过|复发|测试|单测|验证|通过|双证|可发布|批次|并入|\.kt:|正常|快进'
                  } | sort -u | sed "s|^|${f}:|" )
    done < <(git ls-files -- 'docs/*.md' 'docs/roles/*.md' 'docs/roles/*/*.md' 'docs/org/*.md' 'README.md' 'AGENTS.md' \
                 | grep -vE '^(docs/(history/|audit/|generated/|roles/b/|org/PLAN-)|docs/HANDOVER\.md$)')
    if [ "${#stale[@]}" -gt 0 ]; then
        err "活文档过期文案 ${#stale[@]} 处（A-10：旧文件数/旧测试数/退役实例名）："
        printf '      %s\n' "${stale[@]}"
        echo "      改源头文档；历史记录/旧规划豁免（见脚本头注释）"
    else
        ok "活文档无过期文案（A-10）"
    fi

    # 7. 写入范围（A-17）：提交路径 ←→ 职位写入范围
    if [ -z "$ROLE" ]; then
        if [ "$STRICT" = "1" ]; then
            err "A-17：--strict 下必须声明职位（SCOPE_ROLE=<职位|实例名> 或 --role <...>）"
        else
            warn "A-17：未声明职位（SCOPE_ROLE=... 或 --role），跳过写入范围检查"
        fi
    else
        local scope_out scope_rc=0
        scope_out="$(write_scope_paths "$ROLE")" || scope_rc=$?
        case "$scope_rc" in
            0) ;;
            4) err "A-17：写入范围表里没有职位「$ROLE」（见 tools/write_scopes.json）" ;;
            *) warn "A-17：写入范围表读取失败（tools/write_scopes.json），跳过检查" ;;
        esac
        local -a WRITE_PATTERNS=()
        while IFS= read -r pline; do
            [ -n "$pline" ] && WRITE_PATTERNS+=("$pline")
        done <<< "$scope_out"
        if [ "$scope_rc" = "0" ] && [ "${#WRITE_PATTERNS[@]}" -gt 0 ]; then
            local outside_scope=()
            for f in "${staged[@]}"; do
                path_in_patterns "$f" || outside_scope+=("$f")
            done
            if [ "${#outside_scope[@]}" -gt 0 ]; then
                if [ "$STRICT" = "1" ]; then
                    err "A-17：${#outside_scope[@]} 个文件不在「$ROLE」写入范围（--strict 拒绝）："
                else
                    warn "A-17：${#outside_scope[@]} 个文件不在「$ROLE」写入范围（仅警告；代提交/授权须在提交信息标注）："
                fi
                printf '      %s\n' "${outside_scope[@]}"
            else
                ok "A-17：全部暂存文件在「$ROLE」写入范围内"
            fi
        fi
    fi

    # 8. 工作区漂移（警告）
    local dirty
    dirty="$(git status --porcelain | awk 'substr($0,1,1)==" " || substr($0,1,2)=="??"' | wc -l | tr -d ' ')"
    if [ "$dirty" -gt 0 ]; then
        warn "工作区还有 $dirty 处未暂存/未跟踪的改动（可能是队友的，也可能是你还没暂存）"
    fi
    local partial=()
    while IFS= read -r f; do
        [ -n "$f" ] && partial+=("$f")
    done < <(git diff --name-only)
    local both=()
    if [ "${#partial[@]}" -gt 0 ]; then
        for f in "${staged[@]}"; do
            for p in "${partial[@]}"; do
                [ "$f" = "$p" ] && both+=("$f")
            done
        done
    fi
    if [ "${#both[@]}" -gt 0 ]; then
        warn "这些文件同时有已暂存和未暂存内容（可能队友正在改）：${both[*]}"
    fi
}

# ---------- 推送模式 ----------
push_checks() {
    echo "== 推送前检查 =="

    # 0. 考官门禁复位（A-18）：BATCHES 末行待复核/待考官 → 拒绝，除非有考官回执
    if [ "$NO_EXAMINER" = "1" ]; then
        warn "A-18：--no-examiner 跳过考官门禁（仅限非推送/纯清单检查）"
    else
        local last_row
        last_row="$(grep -E '^\|' docs/BATCHES.md 2>/dev/null | tail -1)"
        if printf '%s' "$last_row" | grep -qE '待[^|]*复核|待考官'; then
            if [ -n "$EXAMINER_OK" ]; then
                ok "A-18：BATCHES 末行待复核；考官回执已提供：$EXAMINER_OK"
            else
                err "A-18：BATCHES 末行仍「待复核/待考官」，禁止 push；先取考官结论或带 --examiner-ok=\"<回执摘要>\"（或 EXAMINER_OK 环境变量）"
                echo "      当前末行：$(printf '%s' "$last_row" | cut -c1-80)…"
            fi
        else
            ok "A-18：BATCHES 末行无「待复核/待考官」"
        fi
    fi

    local upstream remote_sha
    upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
    [ -z "$upstream" ] && upstream="origin/master"
    echo "  远端分支：$upstream"

    if git fetch --quiet origin master 2>/dev/null; then
        remote_sha="$(git rev-parse origin/master 2>/dev/null || true)"
    else
        remote_sha=""
        warn "连不上远端：跳过“远端是否被改写”检查（稍后重试）"
    fi

    # 1. 远端有本地没有的提交 = 分叉 / 被 amend / 强推过（INC-005）
    if [ -n "$remote_sha" ]; then
        if git merge-base --is-ancestor "$remote_sha" HEAD; then
            ok "远端没有本地缺失的提交（无需强推）"
        else
            err "远端有本地没有的提交：说明历史被改写过或已分叉（INC-005）"
            echo "      禁止 amend/rebase/reset 已推提交；先 git pull --rebase，"
            echo "      确需强推必须由主持批准并在 docs/history/INCIDENTS.md 留痕。"
        fi
    fi

    # 2. 待推提交：空提交 / 空信息
    if [ -z "$remote_sha" ]; then
        warn "不知道远端 tip，跳过待推提交检查（重试网络后再跑 --push）"
        return
    fi
    local commits=()
    while IFS= read -r c; do
        [ -n "$c" ] && commits+=("$c")
    done < <(git rev-list --no-merges "$remote_sha"..HEAD 2>/dev/null || true)
    if [ "${#commits[@]}" -eq 0 ]; then
        ok "没有待推送的提交"
        return
    fi
    ok "待推送 ${#commits[@]} 个提交"

    local c files msgs=()
    for c in "${commits[@]}"; do
        files="$(git diff-tree --no-commit-id --name-only -r "$c")"
        if [ -z "$files" ]; then
            err "空提交：${c:0:7}（$(git log -1 --format=%s "$c")）"
        fi
        msgs+=("$(git log -1 --format=%B "$c")")
    done

    local i
    for i in "${!commits[@]}"; do
        check_message "${msgs[$i]}" "提交 ${commits[$i]:0:7} 信息"
    done

    # 3. 会不会触发 CI
    local native_hits=()
    for c in "${commits[@]}"; do
        if git diff-tree --no-commit-id --name-only -r "$c" | grep -q '^native-emu/'; then
            native_hits+=("${c:0:7}")
        fi
    done
    if [ "${#native_hits[@]}" -gt 0 ]; then
        echo "  i 本次推送触及 native-emu/**，会触发 CI 构建（${native_hits[*]}）"
    else
        echo "  i 本次推送只改 docs/tools 等，不会触发 CI 构建"
    fi
}

# ---------- 执行 ----------
if [ "$MODE" = "push" ]; then
    push_checks
else
    commit_checks
fi

echo
if [ "$ERRORS" -gt 0 ]; then
    echo "结论：拦住（$ERRORS 个错误，$WARNINGS 个警告）"
    exit 1
fi
if [ "$WARNINGS" -gt 0 ]; then
    echo "结论：通过（$WARNINGS 个警告，确认后再继续）"
else
    echo "结论：通过"
fi
exit 0
