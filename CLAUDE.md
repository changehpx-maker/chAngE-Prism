# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

chAngE_Prism — Prism 制作流程扩展插件。当前包含服务器镜头批量导入、ACES/OCIO 审片转换、Nuke/Houdini Archive 打包和 Daily Review Copy。插件版本为 `v2.3.0`，Windows Prism 2.1.2/2.1.3 是正式验证环境；Nuke Archive 纯核心额外兼容 Nuke 13.2 / Python 3.7，Houdini Archive 支持 Houdini 20.5+。

## 架构

Prism 必需入口保持在 `Scripts/` 根层，业务按 feature 隔离：

```
Scripts/
  Prism_chAngE_Prism_init.py          # 入口，多继承 Variables + Functions
  Prism_chAngE_Prism_Variables.py     # 元数据：版本、平台、serverRoot 配置
  Prism_chAngE_Prism_Functions.py     # 薄门面：注册 Prism 回调并转发到 controller
  change_prism/
    archive_core.py                   # 多 DCC Archive 版本、健康检查、安全删除和扫描
    archive_browser/
      controller.py                   # 统一 Archives 页签注册和刷新
      dialog.py                       # Nuke/Houdini Archive Browser
    config.py                         # Prism 用户配置的共享读写入口
    dcc_paths.py                      # 从 Prism executable override 推导 DCC 辅助程序
    settings/
      controller.py                   # Prism Settings callback 与配置合并
      dialog.py                       # User > chAngE_Prism 配置页
    batch_import/
      controller.py                   # Prism 项目/镜头、导入模式、PDG 与右键菜单编排
      scanner.py                      # 纯逻辑：扫描服务器目录树
      file_processor.py               # published_ref、文件标准化和 review media
      service.py                      # 用户日志与失败报告目录
      pdg.py                          # 单次后台 hython/topcook 与结果监控
      dialog.py                       # Batch Import QDialog
    nuke_archive/
      controller.py                   # Scenefiles 右键和后台任务编排
      service.py                      # Python 3.7 纯核心：解析、复制、版本、健康状态和删除
      dialog.py                       # 预检、进度和 Archive Browser Qt 界面
      cli.py                          # 不依赖 Prism 的命令行入口
    houdini_archive/
      controller.py                   # Scenefiles 右键、Prism 环境和后台任务
      service.py                      # 预检计划、复制、事务和 manifest
      runner.py                       # HIP 版本、hython 选择和 Worker 子进程
      houdini_worker.py               # 唯一允许导入 hou 的模块
      dialog.py                       # Prism 后台 Worker、结果回调和 CLI 预检界面
      cli.py                          # 依赖 hython、不依赖 Prism 的命令行入口
    ocio/
      controller.py                   # 完整窗口和 Media 右键快速转换编排
      service.py                      # 纯逻辑：EXR、OCIO、FFmpeg 和输出路径
      dialog.py                       # ACES/OCIO QDialog 与 QProcess 队列
    review_copy/
      controller.py                   # Project Browser / Media 右键编排
      service.py                      # 当日目录创建、文件/目录复制和失败收集
```

**Batch Import 数据流**：UI 采集输入 → 后台 scanner 扫描服务器 → 创建/打开 Prism 项目 → 创建/更新镜头 → 建立 `published_ref/v####` → 可选复制服务器 step → 标准化 FBX/ABC/XML/MOV 数据和 review media → 可选单次后台 hython/topcook。

**ACES 转换数据流**：EXR 单帧/序列 → `oiiotool --ociodisplay` 烘焙 Display/View → MOV 使用临时 10-bit DPX，MP4-only 使用临时 8-bit 无压缩 TIFF → FFmpeg 编码 MP4/ProRes → 首帧解码验证 → Prism 原生转换输出路径。

**Nuke Archive 数据流**：`.nk` 文本预检 → 标准 Read 路径解析和去重 → 文件数/容量/磁盘空间统计 → 用户确认 → Qt 后台线程复制 → 生成相对路径归档 Nuke 和 manifest → Archive 页签健康检查与版本详情。

**Houdini Archive 数据流**：读取 HIP 保存版本 → 选择兼容 hython → 单次 Worker 加载源 HIP、收集依赖、内存改写并 Save As → 写入 `Incomplete` manifest 后退出 → 普通 Python 按 manifest 后台分块复制 → 文件大小验证并提交 schema 2 manifest → 结果弹窗 → 统一 Archives 页签。

**Daily Review Copy 数据流**：Project Browser 文件或 Media 选择 → 去重 → 创建 `<destination_root>/YYYY-MM-DD/` → 文件覆盖或目录合并 → 汇总失败。

## 关键约定

### 功能模块边界
- `Prism_chAngE_Prism_Functions.py` 只保留 Prism callback、顶层菜单和 controller 转发，不放业务实现
- 新功能放在 `Scripts/change_prism/<feature>/`；Prism 集成写 `controller.py`，纯逻辑写 `service.py` 或明确命名模块，Qt 界面写 `dialog.py`
- feature 之间不直接引用彼此；共享配置和未来公共基础设施放在 `change_prism/` 根层
- controller 懒加载 dialog，避免未使用功能增加 Prism 启动时间
- 每个 feature 在 `tests/` 中有独立测试文件；跨工具真实流程另写 integration test

### Prism 插件加载
- 插件目录必须在 Prism 的 `PRISM_PLUGIN_PATHS` 环境变量中
- Prism 通过 `Prism_<Name>_init.py` 发现插件，调用 `isActive()` 决定是否加载
- 回调通过 `self.core.callbacks.registerCallback(name, method, plugin=self)` 注册

### 服务器目录结构
```
{server_root}/{project}/publish/shot/{episode}/{sequence}/{shot}/{step_category}/{step_code}/
```
- step 映射：`shot_motion/shot_animation` → Animation, `shot_solution/cloth_solution` → Cloth, `shot_solution/hair_solution` → Hair（在 `SERVER_STEPS` 和 `STEP_LABELS` 中定义，预拆分为元组避免重复 split）
- efx 相关内容全部跳过
- 预拆分 `SERVER_STEPS` 为 `[("shot_motion", "shot_animation"), ...]`，避免循环内重复 `split("/")`

### 镜头部门结构
- 每个镜头创建 3 个部门：**FX** (Effects, .hip/Houdini), **Lighting** (Lighting, .hip/Houdini), **Compositing** (Compositing, .nk/Nuke)
- 新镜头：`_ensure_departments(entity)` 创建部门 + category + 预设场景
- 已有镜头：只更新 frame range + metadata，不重建部门/预设（对齐 shot_builder_batch `_try_update_shot` 模式）
- 预设场景通过 `_get_preset_scenes()` 获取，结果缓存在 `self._preset_scenes_cache` 中，整个批次只调一次
- 批量导入时 `getShots(sequence)` 结果按 sequence 缓存在 `shots_cache` 字典中，同 sequence 的镜头只查一次

### 文件处理
- 三种模式：`Create shot only`、引用服务器文件、`Copy to local`
- 非 Create-only 模式创建 `published_ref/v####` 并通过 `saveVersionInfo` 写入标准化数据；复制模式把三个服务器 step 完整复制到该版本
- scanner 递归、大小写不敏感地收集 Animation 的 FBX/MOV/XML 与 Cloth/Hair 的 ABC/MOV/XML
- `.mov` → 通过 `mediaProducts.createIdentifier("review")` + `createVersion()` 创建版本化 media
- 版本号：`getHighestMediaVersion(ctx, getExisting=True)` 获取当前最高版本，`_next_media_version` 通过磁盘检查决定是否递增
- context 构造：必须用 `entity.copy()` 展开 entity 字段到顶层，不能嵌套在 `{"entity": entity}` 下。Prism 模板解析是扁平 key 查找（`"sequence" in context`），嵌套会导致 `@sequence@` 等变量无法解析
- `_increment_version` 防御空值：`ValueError/TypeError` 时 fallback 到 `lowestVersion + 1`
- 同名 review MOV 按 step label 加前缀，避免 Animation/Cloth/Hair 相互覆盖
- shot entity metadata 存 `chAngE_server_project`、`chAngE_server_scene`、`chAngE_server_shot`（服务器侧项目/场景/镜头名），用于右键菜单直接构造服务器路径

### Batch Import PDG
- 仅在用户勾选 `Run PDG FBX Convert` 且本次成功生成 FBX shot data 时启动
- `hython.exe` 从 Prism `getExecutableOverride("Houdini")` 的同目录推导；`topcook.py` 从该 Houdini 安装的 `houdini/python*libs/pdgjob/` 推导，两者不保存到插件配置
- PDG 模板 HIP 和 Houdini package 目录从 `Prism Settings > User > chAngE_Prism` 读取
- 进程环境基于 Prism `startEnv`、Houdini user/project environment，并经过 `preLaunchApp` callback；显式设置 `SHOT_BUILDER_PDG_JSON` 和 `HOUDINI_PACKAGE_DIR`
- 不依赖系统 `PIPELINE_ROOT`；临时 JSON 每次使用独立目录，stdout/stderr 写到 Prism 用户配置目录旁的 `chAngE_Prism/logs/pdg`
- controller 必须懒加载 `pdg.py`，避免 Qt thread/subprocess 代码增加 Prism 启动成本

### 右键菜单
- `openPBShotContextMenu` 添加 "Open Server Folder" 子菜单，含 Animation / Cloth Solution / Hair Solution / Shot Root
- `_open_server_subdir` 从 shot metadata 读 `chAngE_server_project`，直接构造服务器路径，通过 `QDesktopServices.openUrl` 打开
- QMenu 防重复：`onProjectBrowserStartup` 用 `self._chAngE_menu_action` 存储引用，重复触发时先移除旧的再添加

### 层级映射

服务器 3 级（episode/sequence/shot）映射到 Prism 2 级（sequence/shot）：

- Prism `sequence` = 服务器 `episode`（如 `Q2EP007`）
- Prism `shot` = 服务器 `sequence` + `_` + `shot`（如 `SC01_shot001`）

### Filter 输入格式
- `PV001/SC01/shot021` — 完整路径（episode/sequence/shot）
- `SC01/shot021` — 省略 episode（自动区分 ep/seq 还是 seq/shot）
- `shot021` — 仅镜头号
- 支持逗号、换行分隔多行输入

### Frame range
- 从服务器 `shot_animation/xml/description.xml` 解析 `<attribute name="sequence_frame">` 和 `<attribute name="render_start_frame">`
- 不可解析时 fallback 到 `[1001, 1100]`
- 通过 `createEntity(frameRange=[start, end])` 写入 Prism

## 配置

插件设置位于 `Prism Settings > User > chAngE_Prism`，通过 Prism 的
`getConfig`/`setConfig` 和 `userSettings_*` callbacks 持久化。插件根目录
`config.json` 已废弃，运行时不得读取或写入。

| Settings 字段 | 用途 |
|---|---|
| `Server Publish Root` | 服务器根目录；为空时 Windows 默认 `P:\`，其他平台默认测试路径 |
| `Local Projects Root` | 本地 Prism 项目根目录；Batch Import 中手动编辑或浏览选择目录都会立即保存 |
| `Daily Review Destination` | Daily Review Copy 根目录；实际目标为 `<root>/YYYY-MM-DD/` |
| `Hython (from Prism)` | 只读展示；从 Prism Houdini executable override 自动推导，不保存 |
| `PDG Template HIP` | Batch Import PDG 的模板场景 |
| `Houdini Package Directory` | 包含 package JSON 的目录，作为后台进程 `HOUDINI_PACKAGE_DIR` |
| `Current Project OCIO` | 按当前 Prism 项目保存的手动 OCIO config 覆盖 |
| `OCIO` | 没有项目手动覆盖时使用的 OCIO config |
| `PRISM_MEDIA_CONVERSION_OUTPUT_MODE` | ACES 转换输出规则：`same_folder`、`version_suffix` 或 `next_version` |

## ACES / OCIO Media Converter

- 入口：Project Browser 的 `chAngE > ACES / OCIO Media Converter...` 打开完整窗口；Media 预览右键 `ACES / OCIO Quick Convert` 直接启动隐藏队列
- 首版输入限定 RGB EXR 单帧/序列；缺帧或缺 RGB 通道时预检失败
- OCIO 优先级：项目手动覆盖 → `OCIO` 环境变量 → `ocio://default`（界面显示警告）
- 默认 Input 为 `ACEScg`，Display 优先 `Rec.1886 Rec.709`，View 优先 ACES SDR
- MP4：H.264/CRF 18/yuv420p；MOV：ProRes 422 HQ/yuv422p10le，UI 默认 `prores_aw` Fast 并可切换 `prores_ks` Compatibility；均写 BT.709 标签
- OCIO inventory 在窗口显示后加载并按 config/tool 缓存，避免阻塞窗口启动
- 不调用、不复制付费 Media Extension 的代码、二进制、配置或资源
- 完整使用说明见 [ACES转换器.md](ACES转换器.md)

## Nuke Archive

- 入口：镜头 Scenefiles 下 `.nk` 右键 `Package Nuke Archive...`；Project Browser 的 `Archives` 页签浏览版本
- 纯核心和 CLI 仅使用 Python 3.7 标准库，不导入 Prism、Qt、Nuke 或参考工具
- 只解析标准 `Read {}`；支持绝对/相对、引号/大括号、环境变量和 `%04d` / `%d` / `####`
- 图片序列复制整个目录并按规范化源目录去重；MOV/单图只复制文件并按规范化源文件去重；同名不同源追加 `_2` / `_3`
- 归档副本的 Read 使用 `../sequences/...`；Root `project_directory` 使用 Nuke 13 保存格式
- 预检统计文件数、素材容量和目标磁盘空间；空间不足时禁用确认并在执行前再次阻止
- manifest 记录 Read 映射、复制统计、创建信息和源 Nuke 指纹
- Nuke/Houdini manifest 记录源场景的 Department 和 Task；旧 manifest 从 `Scenefiles/<department>/<task>` 推导
- 健康状态优先级：`Incomplete` → `Invalid Manifest` → `Missing Files` → `Source Changed` → `Complete`
- `Open Nuke` 必须走 `core.openFile()`，沿用 Prism 的 Nuke executable override、启动模式和环境
- 新版本写入 `Archives/<task>/v####`，仅按 Task 独立递增，Department 不参与编号；旧 `Archives/v####` 和 `Archives/<department>/<task>/v####` 继续兼容
- 删除按钮永久删除选中的 `v####`；必须二次确认，服务层校验版本父目录、版本名、真实路径和 `.incomplete`
- 完整说明见 [Nuke Archive.md](Nuke%20Archive.md)

## Houdini Archive

- 入口：镜头 Scenefiles 下 `.hip/.hiplc/.hipnc` 右键 `Package Houdini Archive...`；与 Nuke 共用 `Archives` 页签，版本仅按 Task 独立递增
- `houdini_worker.py` 是唯一允许导入 `hou` 的模块；service/CLI 不导入 Prism 或 Qt，运行扫描和 Save As 必须有 Houdini 20.5+ hython
- HIP 版本选择：完全相同 build 优先；只允许同 major/minor 且不低于源 build 的最低版本回退
- 支持 ABC、FBX、非 File Cache VDB、OBJ/GEO/PLY/STL、纹理/HDRI、LUT、音频和序列；序列仅复制匹配模式文件
- File Cache 内部引用和所有 `.bgeo/.bgeo.sc` 固定跳过；USD/Solaris 与 PDG/TOP 动态依赖首版跳过
- 外部 HDA/OTL 仅复制并标记手动激活，不修改 `HOUDINI_OTLSCAN_PATH`
- 新 Archive HIP 直接位于 `Archives/<task>/v####` 根目录，仅重写 `Package Input` 为 `$HIP/dependencies/...`；旧 `hip/` 子目录结构继续兼容
- 统一 Archives 表按 Application、Task 分组，Department 保留为当前版本信息，Version 下拉框默认选择该 Task 的最高版本
- Archives 页签外壳在 Project Browser 启动时创建，Prism EntityWidget 和版本 UI 在首次进入页签时懒加载
- Prism 右键打包无预检/进度窗口；同一源场景禁止重复提交，完成或失败后弹窗
- Prism 流程只启动一次 hython；Worker 写出归档 HIP 和 `Incomplete` manifest 后退出，普通 Python 再按 manifest 复制依赖
- 源文件在 Worker 执行期间发生变化、复制或大小验证失败时清理本次新版本
- 健康状态优先级：`Incomplete` → `Invalid Manifest` → `Missing Files` → `Source Changed` → `Complete with Exclusions` → `Complete`
- 完整说明见 [Houdini Archive.md](Houdini%20Archive.md)

## Daily Review Copy

- 入口：Project Browser 文件右键或 Media 预览右键 `Copy to Daily Review Folder`
- Media 为序列时复制整个序列目录；单文件只复制文件
- 同名文件覆盖；同名目录合并并覆盖冲突文件，不删除目标额外内容
- 批量失败收集源路径和异常，结束时统一 popup

## 测试扫描器

扫描器是纯 Python 模块，可独立运行：

```bash
python3 -c "
from change_prism.batch_import.scanner import scan_server_shots
results = scan_server_shots(r'Z:\publish', ['Q2EP007'], project_code='show')
for r in results:
    print(r['episode'], r['sequence'], r['shot'], [s['label'] for s in r['steps']])
"
```

## 测试

```powershell
python -m unittest discover -s tests -v
$env:PRISM_TEST_ROOT = "D:\pipeline\Prism\Prism_v2.1.3"
python -m unittest tests.test_ocio_integration -v
```

Nuke 13 可选 headless 验证：

```powershell
& "C:\Program Files\Nuke13.2v1\Nuke13.2.exe" --safe -t tests\nuke13_archive_smoke.py
```

Houdini HOM 验证：

```powershell
& "C:\Program Files\Side Effects Software\Houdini 20.5.684\bin\hython.exe" tests\houdini_archive_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 21.0.631\bin\hython.exe" tests\houdini_archive_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" tests\houdini_archive_smoke.py
```

headless/HOM 测试需要对应 DCC 许可证。最近一次 Prism 2.1.3 / PySide6 环境完整扫描共运行 104 项测试，104 项全部通过；Houdini 20.5.684、21.0.631、22.0.368 的 HOM 冒烟测试此前均已通过。

## Prism API 参考

当前 Windows 验证环境的 Prism 源码位于 `D:\pipeline\Prism\Prism_v2.1.3\Scripts`；仓库内 `./prism_docs/` 是官方文档镜像。关键模块：

| 模块 | 用途 |
|---|---|
| `PrismCore.py` | 核心单例：`core.popup()`, `core.openFolder()`, `core.projectBrowser()` |
| `PrismUtils/ProjectEntities.py` | `createEntity()`, `createDepartment()`, `createCategory()`, `getShots()`, `getMetaData()`, `setMetaData()`, `createSceneFromPreset()`, `getPresetScenes()`, `setShotRange()` |
| `PrismUtils/MediaProducts.py` | `createIdentifier()`, `createVersion()`, `getHighestMediaVersion()` — media 版本化 |
| `PrismUtils/Projects.py` | `createProject(name, path, preset)`, `changeProject(configPath)` |
| `PrismUtils/PathManager.py` | `getEntityPath()`, `generateScenePath()` |
| `PrismUtils/Callbacks.py` | `registerCallback()` / `callback()` |
| `PrismUtils/PluginManager.py` | `getPlugin()` - 已加载插件实例 |

`./prism_docs/` 下有 81 个官方文档，`./prism环境变量.md` 有环境变量速查表。

## 已知注意事项

- Qt 信号类型必须精确匹配，`Signal(list)` 不接受 `dict`。用 `Signal(object)` 或直接传回调函数
- `core.projects.createProject()` 对已存在项目会自动被 `changeProject` 替代，不拦截
- 插件通过 `openPBShotContextMenu` 回调添加右键菜单，签名是 `(origin: EntityPage, rcmenu: QMenu, index: QModelIndex)`
- `onProjectBrowserStartup` 回调签名为 `(origin: ProjectBrowser)`。此回调可能多次触发（切换项目等），需防重复添加 widget
- `createDepartment` / `createCategory` 对已存在的会抛异常，用 `try/except: pass` 消音是预期行为
- `getHighestMediaVersion(getExisting=True)` 返回当前最高版本，需手动 +1 得到新版本号；必须传 `mediaType` 键到 context，否则走 `renderVersions` 模板找不到 playblast 版本
- context 传给 `getResolvedProjectStructurePath` 时必须用 `entity.copy()` 展开 entity 字段到顶层，嵌套在 `"entity"` 下会导致模板变量无法解析
- `createSceneFromPreset` 签名因 Prism 版本不同可能不接受 `comment` 参数，需 try/except TypeError 回退
- scanner 中的 `seen` 用于跨 filter 去重，用 `set` 而非 `dict`（key 是 `(project_code, episode, sequence, shot)` 元组）
- scanner 的 `_list_dirs` 有 `@lru_cache`，每次 search 前需调 `clear_list_dirs_cache()` 清除缓存，避免读到旧数据
- 批量导入失败时收集 shot 路径 + 异常信息，结束时在 popup 展示
- Nuke Archive 的 service/CLI 必须维持 Python 3.7：不可使用 `list[str]`、`Path.is_relative_to`、`copytree(dirs_exist_ok=...)` 或结构化模式匹配
- `archive_core.py` 和统一 Archive Browser 需要保持 Python 3.7/Qt5 兼容，不能为了 Houdini 新版本破坏 Nuke 13 环境
- Houdini 依赖扫描和场景修改必须隔离在单次 hython Worker；Prism UI 只提交后台任务并在结束时显示结果
- Archive 健康检查保持快速存在性检查，不在页签刷新时逐帧读取内容或计算校验和；旧 manifest 的容量只在选中版本时临时计算
- Archive 删除是永久操作，目标必须同时通过其版本父目录、`v####`、规范化路径、真实路径和 `.incomplete` 检查
