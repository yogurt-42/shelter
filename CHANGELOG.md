# 开发日志

## 步骤 1 — 窗口骨架

**2026-08**

搭建项目骨架。技术选型 Python + Pygame，独立桌面应用，1100×700 窗口，黑灰白纯色系。

文件结构确定：`main.py` 入口、`config.py` 集中常量、`game_state.py` 唯一数据源、`ui/` 渲染层、`systems/` 逻辑层、`data/` 静态数据。

实现四个核心区域：标签栏（状态/建筑）、资源条（电力/水/食物/废料）、主内容区（状态页日志 + 建筑页 5×6 地图）、底部控制台。

关键设计约定：UI 模块 `draw(surface, state, fonts)` + `handle_*(event, state) -> bool` 统一接口；GameState dataclass 作为唯一状态源；全部可调参数集中 config.py。

## 步骤 1.1 — 地图拖拽 + 迷你日志

建筑页加入鼠标拖拽平移（上下/左右），上下限 ±150px，左右限 0 ~ −600px（防止往右拖动露出房间 1 左侧空白）。采用 grab-and-pull 模型：鼠标往左拖，内容往左移。

建筑页底部新增 75px 迷你日志面板，显示最近 3 条日志。

## 步骤 2 — 资源/事件/命令

资源系统 `resource_system.tick()` 每秒执行：废料 +0.1/s 被动回收。事件系统每 5-15 秒随机从 15 条氛围文案中抽取并写入日志。

命令控制台：`/` 前缀为玩家命令（`/help`、`/status`），`//` 前缀为管理员命令（`//help`、`//clear`、`//hide <tab>`、`//show <tab>`、`//tabs`）。按回车执行，输出写入日志。

状态页日志支持鼠标滚轮滚动，END 键重置滚动位置，TAB 键切换标签。

## 步骤 3 — 裁剪修复 + 分界线 + 标签显隐

修复建筑页内容溢出到上方标签栏和资源条的问题：使用 `surface.set_clip(content_rect)` 裁剪绘制区域。

第 1 层（地表）和第 2 层（地下）之间加入虚线分隔条，替代原来的「地上/地下」文字标注。

建筑页加入横向滚动能力，配合标签显隐命令（`//hide build` / `//show build`），为后续剧情解锁标签页做准备。

## 步骤 4 — 房间系统

### 4.1 数据层
- **房间模板**：8 个模板（发电机/净水/种植/仓库 + 4 个升级版），含建造成本、建造时间、升级/降级链
- **废墟类型**：5 种废墟（轻度/重度/故障设备/密封门/生物危害），可编程清除条件系统（`has_resources`、`has_room`、`stat_check`）
- 房间状态机 5 态：EMPTY → BUILDING → BUILT，RUIN → CLEARING → EMPTY

### 4.2–4.6 弹窗与交互
- 弹窗系统 `popup.py`：半透明黑色遮罩 + 居中面板，Esc 关闭
- 建造弹窗：卡片式布局，每房间 2 行（名称+费用 / 描述），点击建造扣资源启动计时器
- 废墟弹窗：显示名称/描述/消耗/清除条件/开始清理按钮
- 房间信息弹窗：显示工种/产出/消耗/升级方向
- 操作菜单弹窗：右键房间 → 升级/降级/拆除

### 资源系统改造
- 房间产出按在岗工人 × 每工人产出率 × dt 计算
- 仓库类被动消耗按房间计数自动扣除

## 步骤 5 — 人口与工种分配

引入工种聚合模型：房间不直接分配工人，而是按工种类型汇总岗位。例如 2 个发电机 = 4 个「电力技术员」岗位。

新增 `data/job_types.py`：6 种工种（电力技术员/高级电力工程师/净水技术员/高级净水工程师/种植员/水培技术员），每工种独立定义产出/消耗率。

新增人口标签页：按工种显示在岗/总岗位 + [−]/[+] 按钮。空闲工人 = 总人口 − 已分配。

资源系统改为双重模型：A. 工种产出（按在岗工人× 工种率），B. 被动消耗（按房间数×固定率）。

仓库等无工种房间设 `job_slots=0`，通过 `passive_consumption` 消耗资源维持运转。

## 步骤 5.1 — UI 修复

- 所有弹窗中的资源键名从中文化显示（scrap→废料, power→电力, water→水, food→食物）
- 减号字符 `−` (U+2212) 更换为 ASCII `-`，修复 SimHei 字体渲染方框问题
- 建造/清理/升级操作增加全资源检查（之前只检查废料），资源不足时给出具体提示

## 步骤 5.2 — 管理员模式

新增 4 条管理模式命令和 2 个 GameState 标记：

| 命令 | 效果 |
|------|------|
| `//i am infinite` | 无限资源 — 无视资源消耗、上限、费用检查 |
| `//full speed` | 极速建造 — 所有建造/清理等待时间归零 |
| `//it is enough` | 退出全部管理模式 |
| `//i am 42` | 一键开启全部管理模式 |

- `resource_system.py`：`infinite_resources` 时跳过资源扣除和上限钳制
- `popup.py`：`_check_resources` / `_deduct_resource` 在无限资源模式下跳过
- `main.py`：`_tick_construction` 在极速模式下即刻完成所有在建项目
- `game_state.py`：新增 `infinite_resources` / `full_speed` bool 字段
- `console.py`：支持多词命令匹配（`i am infinite`、`full speed` 等）
- `+`/`-` 按钮改为 `pygame.draw.rect` 绘制的图形符号，彻底消除字体依赖

## 步骤 5.3 — 存档系统

实现 pickle 序列化存档，3 个槽位，文件保存在 `saves/slot_N.sav`。

**新增文件**：`shelter/save_system.py`
- `save_game(state, slot)` — 序列化 GameState + 元数据
- `load_game(slot)` — 反序列化，重置计时器
- `list_saves()` — 扫描所有槽位返回元数据
- `delete_save(slot)` — 删除存档文件

**新增命令**：`/save [slot]`、`/load [slot]`、`/saves`

**实现细节**：
- `/load` 通过 `__dict__` 原地替换当前 state，保持引用不变
- `load_game` 自动重置 `start_time` / `last_resource_tick` / `last_event_time` 避免时间跳跃
- 启动时检测现有存档，有则日志提示
- 后续计划：设置标签页（TAB_SETTINGS）提供图形化存档管理

## 步骤 6 — 物资系统

新增"物资"标签页，将资源与物品分离显示与管理。

**资源侧：**
- 为废料补充独立上限 `max_scrap`，初始 `INITIAL_MAX_SCRAP=300`
- 仓库/大型仓库建造完成后通过 `on_built_effect` 提升废料上限（+50 / +100）
- `resource_system.py` 的 `_add_resource()` 与 `_clamp_resources()` 统一处理废料上限

**物品侧：**
- 新增文件 `shelter/data/items.py`：定义 `ITEM_DEFINITIONS`，先加入 `test_item_a` / `test_item_b`
- `GameState` 新增 `items: dict[str,int]` 与 `max_items: int`（共享格子上限，初始 20）
- `GameState.total_item_slots()` / `can_add_item()` / `add_item()` / `remove_item()` 方法
- 废墟清理完成时按 `rewards` 发放物品；物品栏满时部分奖励丢失并日志提示
- 新增管理员测试命令 `//give <item_key> [count]`

**UI 侧：**
- 新增 `shelter/ui/materials_tab.py`：上半显示 4 资源 `x / y`，分隔线后显示物品 `a / b` 与物品列表
- 注册新标签 `TAB_MATERIALS=3`，默认可见，支持点击切换与 `TAB` 键循环
- 更新 `main.py` 鼠标点击路由、`renderer.py` 绘制分支、`console.py` 标签名映射

## 步骤 7 — 地图扩大与视野系统

按 `map.xlsx` 设计扩大地图并引入视野/迷雾机制。

**地图尺寸：**
- `FLOORS` 从 5 改为 4，`ROOMS_PER_FLOOR` 从 6 改为 10
- 每层房间数可不等，空单元格用 `None` 表示 void
- `BUILD_DRAG_LIMIT_X` 扩大至 800，保证 10 列地图可横向拖动

**新房间/废墟：**
- `data/rooms.py`：新增不可建造的 `gate`（避难所大门）与 `elevator`（电梯井）
- `data/ruins.py`：新增 `elevator_ruin`（损坏电梯井），带 `clears_to: "elevator"`
- 普通废墟增加可选 `clears_to` 字段；清理后可直接变为对应建成房间

**视野规则：**
- room slot 增加 `revealed`（已揭示）与 `void`（无房间）字段
- `EMPTY` / `BUILT` 房间揭示同层左右邻居
- `elevator` 房间额外揭示上下对齐的电梯房间；非电梯邻居不可见
- 清理废墟后变为 `EMPTY`（或 `clears_to` 目标房间），从而继续扩展视野
- `void` 单元格不渲染、不交互；未揭示单元格显示为空方框，不显示状态/废墟/条件

**数据驱动布局：**
- 移除固定的 `INITIAL_RUIN_LAYOUT`
- 新增 `INITIAL_FLOOR_LAYOUT`，按楼层列出每个格子的初始状态与是否揭示
- `GameState._init_floors()` 读取该表初始化；`GameState._propagate_vision()` 级联计算视野

**UI 适配：**
- `build_tab.py`：void 跳过绘制；未揭示格只画空方框；点击忽略未揭示/void
- 建筑标签页支持鼠标滚轮缩放，范围 `0.5x ~ 2.0x`，拖动边界随缩放动态计算
- 层数文字改为与房间单元格垂直居中对齐
- `popup.py`：拆除房间后调用 `_refresh_vision()`

---

## 步骤 8 — 项目结构解耦与剧情系统扩展性改造

**2026-08-18**

重构核心模块，将业务逻辑从 `GameState` 与 UI 中剥离，并泛化剧情系统以支持后续剧情、选项与事件。

**房间系统解耦：**
- 新增/重写 `shelter/systems/room_system.py`，集中所有房间生命周期操作：
  - 楼层初始化、视野传播、容量重算
  - `start_building` / `start_clearing` / `complete_construction`
  - `get_upgrade_options` / `apply_room_action`（升级、维修、降级、拆除）
  - 通用资源检查 `check_resources` / `deduct_resources`
- `shelter/game_state.py` 瘦身：移除房间/视野/容量业务方法，保留纯状态与通用辅助方法
- `shelter/ui/popup.py` 不再直接修改 `state.floors` 或扣资源，所有房间动作通过 `room_system` 执行
- `shelter/main.py` 的 `_tick_construction` 改为调用 `room_system.complete_construction`

**剧情系统扩展性：**
- 将 `intro_*` 字段全部改为 `story_*`，新增 `story_queue`、`story_flags`、`story_popup_mode`、`story_choices`
- 重写 `shelter/systems/story_system.py`：
  - `play_story(state, story_key)` 支持任意剧情与排队
  - 内置 action：`log`、`unlock_tab`、`unlock_blueprint`、`flag`、`choice`、`condition`、`end_story`
  - `register_action(name, handler)` 可注册自定义 action
  - `choose(state, choice_index)` 处理选项分支
- `shelter/ui/popup.py`：tutorial popup 改为 story popup，支持 `info` 和 `choice` 两种模式
- `shelter/data/stories.py`：`end_intro` 改为 `end_story`
- `shelter/save_system.py`：新增 `intro_*` → `story_*` 字段迁移，保持旧存档可读

**验证：**
- 编译检查通过
- 游戏可正常启动并运行 5 秒无报错
- 临时 smoke test 覆盖：初始化、房间维修、剧情 tick、剧情选项分支，全部通过

---

## 技术决策记录

- **纯 dataclass 而非 ECS**：当前规模下 dataclass 更简单，无需引入 ECS 框架
- **UI 模块无状态**：所有 UI 状态放 GameState（如 `build_view_offset_x`），模块级只保留拖拽中间变量
- **业务逻辑下沉到 systems/**：`GameState` 只存状态，房间操作在 `room_system`，剧情推进在 `story_system`
- **popup 覆盖而非新窗口**：弹窗在同一 Pygame surface 上层绘制，使用半透明遮罩
- **工种独立于房间**：产出率由工种定义而非房间模板，使同类房间的岗位可聚合
- **剧情数据驱动**：所有剧情事件写在 `data/stories.py`，运行时由 `story_system` 驱动，便于后续扩展选项与分支
- **存档字段迁移**：`load_game` 负责旧字段到新字段的兼容，避免 GameState 被历史字段污染
