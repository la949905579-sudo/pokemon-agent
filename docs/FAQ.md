# FAQ · 常见问题

## 安装

**Q: 提示 "应用未安装 / 签名不一致"**
A: 旧版本不是同一个签名。卸载旧版再装，或从 `MENU → 更新` 走 OTA（签名已固定）。

**Q: 提示 "解析软件包时出现问题 (33) / packageInfo is null"**
A: APK 下载不完整或下到的是错误页。重新下载；OTA 失败先关 VPN 再试。

**Q: OTA 装的时候没反应**
A: 首次需要允许「安装未知应用」：设置 → 应用 → NativeEmu → 安装未知应用 → 允许。

## 运行

**Q: 上屏黑屏**
A: 1) 是否在后台暂停过？点「继续」；2) 切后台再回来 surface 会重建，代码已处理，若仍黑屏重开 App；3) 看 `/sdcard/Download/emu_native.log` 最后一步。

**Q: 画面颜色不对 / 左右重复**
A: 像素格式问题（RGB565 vs 32 位）。当前版本已修；若复现，看日志里 `bytesPerPixel` 是多少。

**Q: ROM 列表是空的**
A: 没给「所有文件访问」权限：设置 → 应用 → NativeEmu → 权限 → 所有文件访问。

**Q: 已加载 ROM，再选别的 ROM 不生效**
A: 已修复（`if (core_) return true` 拦截了重新初始化）。旧版本请升级。

**Q: 按键不灵 / 同时按两个键只有一个生效**
A: 已修复（多指按 pointerId 跟踪 + 按钮真实坐标命中）。旧版本升级。

## 连接（TCP 桥）

**Q: Python 连 `127.0.0.1:55401` 超时**
A: 1) App 是否在前台或保活中（后台被冻住会超时）；2) 设置省电策略为「无限制」+ 自启动；3) 首次连接慢是正常的。

**Q: 桥连上了但 read 返回全 0**
A: 地址不对（不同游戏/版本地址不同），先读 ROM 头 `0x080000A0` 验证通道。

## 自动化

**Q: 怎么从 RetroArch 切到 NativeEmu**
A: `EMU_BACKEND=native python3 farm.py ...`；不设置就还是走 RetroArch UDP。

**Q: 下屏队伍是空的**
A: 还没拿到宝可梦（游戏进度），或 `push_status.py` 没在跑。

## 战斗与下屏

**Q: 进战斗了但下屏没切战斗页**
A: 需要 Python 推送或本地状态读到 `battle`。检查 `bash /root/workspace/start_push.sh` 是否在跑；新版下屏也会直接读本地内存。

**Q: 出招后下屏跳回地图**
A: 已修（动画阶段映射为 `battle_anim` + 4 秒滞回）。旧版请更新。

**Q: 点小地图会直接走吗**
A: 会（180ms/步）。注意这是真按键，会移动角色。

## 构建

**Q: 构建一直 queued**
A: GitHub Actions 排队拥堵，等或手动 rerun。

**Q: 构建失败自动发布旧包**
A: 已修（publish_release 检查 run 结论）。
