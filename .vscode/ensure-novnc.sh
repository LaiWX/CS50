#!/usr/bin/env bash

set -Eeuo pipefail

readonly display_name=":1"
readonly vnc_port="5901"
readonly novnc_port="6080"
readonly novnc_web_root="/usr/share/novnc"
readonly current_uid="$(id -u)"
readonly runtime_parent="${XDG_RUNTIME_DIR:-/tmp}"
readonly runtime_dir="${runtime_parent}/cs50-novnc-${current_uid}"
readonly xtigervnc_pid_file="${runtime_dir}/xtigervnc.pid"
readonly openbox_pid_file="${runtime_dir}/openbox.pid"
readonly websockify_pid_file="${runtime_dir}/websockify.pid"
readonly xtigervnc_log="${runtime_dir}/xtigervnc.log"
readonly openbox_log="${runtime_dir}/openbox.log"
readonly websockify_log="${runtime_dir}/websockify.log"

fail() {
  printf 'noVNC 启动失败: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "缺少命令: $1"
}

prepare_runtime_dir() {
  if [[ -L "$runtime_dir" ]]; then
    fail "运行时路径不能是符号链接: $runtime_dir"
  fi
  if [[ -e "$runtime_dir" && ! -d "$runtime_dir" ]]; then
    fail "运行时路径不是目录: $runtime_dir"
  fi

  (umask 077 && mkdir -p "$runtime_dir")
  [[ "$(stat -c '%u' "$runtime_dir")" == "$current_uid" ]] || \
    fail "运行时目录不属于当前用户: $runtime_dir"
  chmod 700 "$runtime_dir"
}

remove_empty_legacy_vnc_dir() {
  local account_home legacy_vnc_dir

  account_home="$(getent passwd "$current_uid" | awk -F: 'NR == 1 { print $6 }')"
  [[ "$account_home" == /* && "$account_home" != "/" ]] || \
    fail "无法安全解析当前用户的主目录"
  legacy_vnc_dir="${account_home}/.vnc"

  [[ -e "$legacy_vnc_dir" ]] || return 0
  if [[ -L "$legacy_vnc_dir" || ! -d "$legacy_vnc_dir" ]]; then
    fail "旧 VNC 路径不是普通目录，拒绝删除: $legacy_vnc_dir"
  fi
  [[ "$(stat -c '%u' "$legacy_vnc_dir")" == "$current_uid" ]] || \
    fail "旧 VNC 目录不属于当前用户，拒绝删除: $legacy_vnc_dir"
  if find "$legacy_vnc_dir" -mindepth 1 -print -quit | grep -q .; then
    fail "Xtigervnc 在 $legacy_vnc_dir 产生了文件，已保留现场"
  fi

  rmdir -- "$legacy_vnc_dir"
}

managed_pid() {
  local pid_file="$1"
  local expected_command="$2"
  local pid command_line

  [[ -r "$pid_file" ]] || return 1
  read -r pid < "$pid_file"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  command_line="$(tr '\0' ' ' < "/proc/${pid}/cmdline" 2>/dev/null)" || return 1
  [[ "$command_line" == *"$expected_command"* ]]
}

remove_stale_pid_file() {
  local pid_file="$1"
  local expected_command="$2"
  local pid

  [[ -e "$pid_file" ]] || return 0
  if managed_pid "$pid_file" "$expected_command"; then
    return 0
  fi

  read -r pid < "$pid_file" || true
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    fail "PID 文件 $pid_file 指向无关进程 $pid，拒绝覆盖"
  fi
  rm -f -- "$pid_file"
}

port_is_listening() {
  ss -H -ltn "sport = :$1" 2>/dev/null | grep -q .
}

assert_loopback_listener() {
  local port="$1"

  port_is_listening "$port" || fail "端口 $port 尚未就绪"
  if ! ss -H -ltn "sport = :$port" 2>/dev/null | \
    awk '$4 !~ /^(127\.0\.0\.1|\[::1\]):/ { bad = 1 } END { exit bad }'; then
    fail "端口 $port 不是仅回环监听，拒绝继续"
  fi
}

wait_for_display() {
  local attempt
  for attempt in {1..50}; do
    if xdpyinfo -display "$display_name" >/dev/null 2>&1; then
      return 0
    fi
    if ! managed_pid "$xtigervnc_pid_file" "Xtigervnc"; then
      tail -n 30 "$xtigervnc_log" >&2 2>/dev/null || true
      fail "Xtigervnc 在显示器就绪前退出"
    fi
    sleep 0.2
  done
  fail "等待显示器 $display_name 超时，日志: $xtigervnc_log"
}

wait_for_novnc() {
  local attempt
  for attempt in {1..50}; do
    if curl --fail --silent --max-time 1 \
      "http://127.0.0.1:${novnc_port}/vnc.html" >/dev/null; then
      return 0
    fi
    if ! managed_pid "$websockify_pid_file" "websockify"; then
      tail -n 30 "$websockify_log" >&2 2>/dev/null || true
      fail "websockify 在 noVNC 就绪前退出"
    fi
    sleep 0.2
  done
  fail "等待 noVNC 超时，日志: $websockify_log"
}

start_xtigervnc() {
  if managed_pid "$xtigervnc_pid_file" "Xtigervnc"; then
    xdpyinfo -display "$display_name" >/dev/null 2>&1 || \
      fail "Xtigervnc 进程存在但显示器 $display_name 不可用"
    assert_loopback_listener "$vnc_port"
    return 0
  fi

  if xdpyinfo -display "$display_name" >/dev/null 2>&1 || port_is_listening "$vnc_port"; then
    fail "显示器 $display_name 或端口 $vnc_port 已被未管理的进程占用"
  fi

  Xtigervnc "$display_name" \
    -localhost=1 \
    -SecurityTypes=None \
    -rfbport "$vnc_port" \
    -geometry 1280x800 \
    -depth 24 \
    -noreset \
    >"$xtigervnc_log" 2>&1 &
  printf '%s\n' "$!" > "$xtigervnc_pid_file"

  wait_for_display
  assert_loopback_listener "$vnc_port"
}

start_openbox() {
  if managed_pid "$openbox_pid_file" "openbox"; then
    return 0
  fi

  DISPLAY="$display_name" openbox-session \
    >"$openbox_log" 2>&1 &
  printf '%s\n' "$!" > "$openbox_pid_file"

  sleep 0.2
  if ! managed_pid "$openbox_pid_file" "openbox"; then
    tail -n 30 "$openbox_log" >&2 2>/dev/null || true
    fail "Openbox 启动失败"
  fi
}

start_websockify() {
  if managed_pid "$websockify_pid_file" "websockify"; then
    wait_for_novnc
    assert_loopback_listener "$novnc_port"
    return 0
  fi

  if port_is_listening "$novnc_port"; then
    fail "端口 $novnc_port 已被未管理的进程占用"
  fi

  websockify \
    --web "$novnc_web_root" \
    "127.0.0.1:${novnc_port}" \
    "127.0.0.1:${vnc_port}" \
    >"$websockify_log" 2>&1 &
  printf '%s\n' "$!" > "$websockify_pid_file"

  wait_for_novnc
  assert_loopback_listener "$novnc_port"
}

stop_managed_process() {
  local pid_file="$1"
  local expected_command="$2"
  local pid

  managed_pid "$pid_file" "$expected_command" || return 0
  read -r pid < "$pid_file"
  kill -TERM "$pid" 2>/dev/null || true
}

cleanup() {
  local attempt pid_file expected_command pid

  trap - EXIT INT TERM HUP
  stop_managed_process "$websockify_pid_file" "websockify"
  stop_managed_process "$openbox_pid_file" "openbox"
  stop_managed_process "$xtigervnc_pid_file" "Xtigervnc"

  for attempt in {1..20}; do
    if ! managed_pid "$websockify_pid_file" "websockify" && \
      ! managed_pid "$openbox_pid_file" "openbox" && \
      ! managed_pid "$xtigervnc_pid_file" "Xtigervnc"; then
      break
    fi
    sleep 0.1
  done

  for pid_file in "$websockify_pid_file" "$openbox_pid_file" "$xtigervnc_pid_file"; do
    case "$pid_file" in
      "$websockify_pid_file") expected_command="websockify" ;;
      "$openbox_pid_file") expected_command="openbox" ;;
      *) expected_command="Xtigervnc" ;;
    esac
    if managed_pid "$pid_file" "$expected_command"; then
      read -r pid < "$pid_file"
      kill -KILL "$pid" 2>/dev/null || true
    fi
    read -r pid < "$pid_file" 2>/dev/null || pid=""
    if [[ "$pid" =~ ^[0-9]+$ ]]; then
      wait "$pid" 2>/dev/null || true
    fi
    rm -f -- "$pid_file"
  done

  # Xtigervnc 可能在退出时再次创建空的 ~/.vnc。
  remove_empty_legacy_vnc_dir || true
}

supervise_services() {
  while sleep 2; do
    managed_pid "$xtigervnc_pid_file" "Xtigervnc" || \
      fail "Xtigervnc 意外退出，日志: $xtigervnc_log"
    managed_pid "$openbox_pid_file" "openbox" || \
      fail "Openbox 意外退出，日志: $openbox_log"
    managed_pid "$websockify_pid_file" "websockify" || \
      fail "websockify 意外退出，日志: $websockify_log"
    remove_empty_legacy_vnc_dir
  done
}

main() {
  local command
  printf '正在准备 noVNC\n'

  for command in Xtigervnc openbox-session websockify xdpyinfo curl ss awk grep \
    stat getent find rmdir; do
    require_command "$command"
  done
  [[ -f "$novnc_web_root/vnc.html" ]] || \
    fail "找不到 noVNC 页面: $novnc_web_root/vnc.html"

  prepare_runtime_dir
  trap cleanup EXIT
  trap 'exit 0' INT TERM HUP
  remove_stale_pid_file "$xtigervnc_pid_file" "Xtigervnc"
  remove_stale_pid_file "$openbox_pid_file" "openbox"
  remove_stale_pid_file "$websockify_pid_file" "websockify"

  start_xtigervnc
  start_openbox
  start_websockify
  remove_empty_legacy_vnc_dir

  printf '\nnoVNC 已就绪: http://localhost:%s/vnc.html?autoconnect=1&resize=scale\n' \
    "$novnc_port"
  supervise_services
}

main "$@"
