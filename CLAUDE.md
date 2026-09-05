# CLAUDE.md

本文件只记录编码代理必须遵守的项目约束。功能操作、产品行为和验收细节放在对应功能文档中，避免这里与实现重复或过期。

## 项目与兼容边界

`chAngE_Prism` 是 Prism 2 制作流程扩展，正式环境为 Windows Prism 2.1.2/2.1.3。

- Nuke Archive 纯核心兼容 Nuke 13.2 / Python 3.7。
- Houdini Archive 支持 Houdini 20.5+。
- Qt 代码同时考虑 Qt5/PySide2 与 Qt6/PySide6。
- 插件版本的唯一代码来源是 `Scripts/Prism_chAngE_Prism_Variables.py`，不要在本文件维护版本号。
- 部署目录名必须与入口文件前缀一致：Prism 按**目录名**拼模块名
  （目录 `chAngE_Prism` → 导入 `Prism_chAngE_Prism_init`）。目录名改成
  `change_prism` 之类会导致 `ModuleNotFoundError: No module named
  'Prism_change_prism_init'`，插件整个加载失败。

## 架构

Prism 必需入口位于 `Scripts/` 根层，业务位于 `Scripts/change_prism/`：

```text
Prism_chAngE_Prism_init.py
Prism_chAngE_Prism_Variables.py
Prism_chAngE_Prism_Functions.py
change_prism/
  config.py
  dcc_paths.py
  houdini_asset_bridge.py
  archive_core.py
  <feature>/
    controller.py
    service.py
    dialog.py
    cli.py          # 仅需要独立命令行时存在
```

功能路由：

| 功能 | 代码目录 | 详细文档 |
|---|---|---|
| Batch Import / PDG | `change_prism/batch_import/` | [Batch Import.md](Batch%20Import.md) |
| Asset Library | `change_prism/asset_library/` | [Asset Library.md](Asset%20Library.md) |
| ACES / OCIO | `change_prism/ocio/` | [ACES转换器.md](ACES转换器.md) |
| Nuke Archive | `change_prism/nuke_archive/` | [Nuke Archive.md](Nuke%20Archive.md) |
| Houdini Archive | `change_prism/houdini_archive/` | [Houdini Archive.md](Houdini%20Archive.md) |
| Archive Browser | `change_prism/archive_browser/` | Nuke/Houdini Archive 文档 |
| Daily Review Copy | `change_prism/review_copy/` | [README.md](README.md) |
| Prism Settings | `change_prism/settings/` | [README.md](README.md) |

## 强制架构约定

- `Prism_chAngE_Prism_Functions.py` 必须保持为薄回调门面，只注册 callback、创建顶层菜单并转发 controller。
- 新功能按 `controller.py + service.py + dialog.py` 拆分；纯逻辑不得依赖 Qt 或 Prism。
- feature 之间不直接导入彼此。共享配置、DCC 路径和 Archive 基础设施放在 `change_prism/` 根层。
- controller 必须懒加载 dialog、重型库和可选子进程模块，避免拖慢 Prism 启动。
- 长时间扫描、缩略图、媒体转换、DCC 启动和大文件复制不得阻塞 GUI 线程。
- 每个 feature 有独立单元测试；需要真实 Nuke/Houdini 的流程放在 smoke/integration test。

## Prism API 易错规则

- Prism context 必须以 `entity.copy()` 为基础，把 `sequence`、`shot` 等字段展开到顶层；不得嵌套为 `{"entity": entity}`。
- media 版本化使用 `identifierType="playblasts"`，context 同时包含 `mediaType="playblasts"`。
- `_increment_version` 遇到空值或非法版本时回退到 `lowestVersion + 1`。
- `createSceneFromPreset` 在不同 Prism 版本中签名不同；`comment` 参数需有 `TypeError` 回退。
- `createDepartment` / `createCategory` 的“已存在”异常可以消音，其他异常不要无条件吞掉。
- `onProjectBrowserStartup` 可能多次触发；菜单和页签注册必须防重复。
- 批量操作逐项收集路径和异常，结束后统一报告，不因单项失败丢失其余结果。
- Qt 跨线程信号使用准确类型；不确定结果形状时用 `Signal(object)`。`QPixmap` 只能在 GUI 线程创建。

## 配置约定

- 工作站路径统一保存到 `Prism Settings > User > chAngE_Prism`，通过 Prism `getConfig`/`setConfig` 和 `userSettings_*` callback 持久化。
- 不读取或写入插件根目录 `config.json`，也不要把用户机器绝对路径硬编码进运行时代码。
- 当前项目 OCIO 的内部 key 使用规范化项目路径；UI 显示保留 Prism 原始路径大小写。
- Batch Import 的 Hython 从 Prism Houdini executable override 推导，`topcook.py` 从同一安装目录查找；不保存 `hython_path` 或 `topcook_path`。
- 运行诊断文件统一放在 `%TEMP%\chAngE_Prism\<feature>\logs|json\`。PDG 为每次运行创建独立的 `batch_import\pdg\json\change_prism_pdg_<随机>\shot_data.json`，通过 `SHOT_BUILDER_PDG_JSON` 和 `HOUDINI_PACKAGE_DIR` 显式传入 Hython，已启动的运行结束后保留 JSON；不要求系统 `PIPELINE_ROOT`。
- Asset Library sources 是 Prism 用户全局配置，不写入项目配置。

## Batch Import 不变量

- 服务器路径为：

```text
{server_root}/{project}/publish/shot/{episode}/{sequence}/{shot}/{step_category}/{step_code}/
```

- `SERVER_STEPS` 固定映射 Animation、Cloth、Hair；`_list_dirs` 有 `lru_cache`，每次 search 前必须调用 `clear_list_dirs_cache()`。
- Prism `sequence` = 服务器 `episode`；Prism `shot` = `<server_sequence>_<server_shot>`。
- Batch Import 的 Shotinfo 只保存帧范围，不写入镜头 metadata。
- 同 sequence 的 `getShots()` 结果按批次缓存；新建镜头后同步更新缓存。
- Review MOV 通过 Prism media API 导入；同名文件必须避免覆盖。
- PDG 模块保持懒加载，只在用户启用且存在成功 FBX 数据时启动一次后台 Hython。
- PDG JSON 只包含 FBX、帧范围和 Animation XML 的必要 metadata；Cloth/Hair 仅传递 XML 路径，不传递 attributes 或 elements。

其余扫描格式、三种导入模式、`published_ref` 和 PDG JSON 结构以 [Batch Import.md](Batch%20Import.md) 为准。

## Archive 不变量

- `archive_core.py`、Archive Browser 和 Nuke Archive 核心保持 Python 3.7 / Qt5 兼容。
- Nuke `service.py`/CLI 只用 Python 3.7 标准库，不导入 Prism、Qt 或 Nuke；禁止 `list[str]`、`Path.is_relative_to()`、`copytree(dirs_exist_ok=...)` 和结构化模式匹配。
- Archive 的 `hou` 只能在 `houdini_archive/houdini_worker.py` 中导入；依赖扫描、路径改写和 Save As 在单次 Hython Worker 中完成。`houdini_asset_bridge.py` 是唯一例外，只能在 Houdini 交互进程中按用户明确动作懒加载 `hou`。
- Archive 永远不修改原始 DCC 场景。新 Archive 使用事务目录，失败或取消时只清理本次新版本。
- Archive 版本仅按 Task 独立递增；Department 只作为元数据。必须继续读取旧 Archive 布局和旧 manifest。
- Archive 刷新只做快速存在性检查，不逐帧读素材或计算校验和。
- Archive 删除是永久操作，必须同时验证 Archives 根、版本父目录、`v####`、规范化路径、真实路径和 `.incomplete` 状态。

## Asset Library 与媒体不变量

- Asset Library 完整 UI 和扫描器首次进入页签后再加载。
- 扫描不得跟随链接目录，必须排除 `_thumbs`；后台结果使用 generation 校验，过期结果不能覆盖新配置。
- 缩略图只由用户手动触发；后台总并发最多 4 个，其中 HDR/EXR 最多 2 个；浏览和刷新只读取缓存。
- Remove Source 只改配置，不删除素材或 `_thumbs`。
- Houdini HDRI 动作只能由 Asset Library GUI 主线程触发，不得从扫描或缩略图线程调用 `hou`；目标优先取当前可见 Network Editor 的 `pwd()`，无 Network Editor 时才回退 `hou.pwd()`，网络类别必须使用 `childTypeCategory()` 判断。
- Object 网络创建原生 `envlight`，LOP 网络创建 `domelight::3.0`；只引用当前 Active Location 的绝对路径，不复制素材或自动保存 HIP。
- ACES/OCIO 转换不得调用、复制或依赖付费 Media Extension 的代码、二进制和资源。
- Daily Review 目录复制采用合并覆盖，不删除目标中额外内容。

## 测试

通用单元测试：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Qt 测试应在 Prism 自带 Python/PySide 环境运行。真实 DCC 验证入口：

- Nuke 13：`tests/nuke13_archive_smoke.py`
- Houdini：`tests/houdini_archive_smoke.py`
- Houdini Asset Library：`tests/houdini_asset_library_smoke.py`
- OCIO bundled tools：`tests/test_ocio_integration.py`

不要在本文记录“当前通过多少项”或具体安装 build；测试结果和本机路径会过期。

## 参考

- [README.md](README.md)：用户入口、配置和功能总览
- [开发需求.md](开发需求.md)：需求范围与实现状态
- [prism环境变量.md](prism环境变量.md)：环境变量速查
- `prism_docs/`：仓库内 Prism 官方文档镜像
- `tests/`：当前行为和兼容性约束的可执行说明
