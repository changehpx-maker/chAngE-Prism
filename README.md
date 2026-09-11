# chAngE_Prism

`chAngE_Prism v2.5.1` 是基于 Prism 2 的制作流程扩展插件，当前主要服务于镜头批量创建、外部图片资产管理、审片媒体、ACES/OCIO 转换以及 Nuke/Houdini Archive 打包。

Windows Prism 2.1.2/2.1.3 是当前正式验证环境。Nuke Archive 纯核心额外兼容 Nuke 13.2 的 Python 3.7；Houdini Archive 和 Asset Library 环境光支持 Houdini 20.5+。

## 当前功能

| 功能 | Prism 入口 | 用途 |
|---|---|---|
| Batch Import | `chAngE > Batch Import from Server...` | 扫描 Animation/Cloth/Hair 发布，创建镜头和 `published_ref`，可复制到本地并后台执行 PDG FBX Convert |
| ACES / OCIO Converter | `chAngE > ACES / OCIO Media Converter...`；Media 右键快速转换 | 将 RGB EXR 单帧/序列转换为 H.264 MP4 或 ProRes MOV |
| Archives | Project Browser 的 `Archives` 页签 | 统一浏览、打开、检查和删除 Nuke/Houdini Archive |
| Asset Library | Project Browser 的 `Asset Library` 页签 | 以外部目录源管理和浏览 HDR/EXR 及常用图片，不复制素材 |
| Nuke Archive | Scenefiles 中 `.nk` 右键 | 文本解析标准 Read，复制依赖并生成相对路径 Nuke Archive |
| Houdini Archive | Scenefiles 中 `.hip/.hiplc/.hipnc` 右键 | 单次 hython 收集、改写并另存场景，退出后由普通 Python 按 manifest 复制依赖 |
| Daily Review Copy | Project Browser 文件右键；Media 预览右键 | 将选择内容复制到配置根目录下的当天日期文件夹 |

## 目录结构

```text
Scripts/
  Prism_chAngE_Prism_init.py
  Prism_chAngE_Prism_Variables.py
  Prism_chAngE_Prism_Functions.py
  change_prism/
    archive_core.py
    archive_browser/
      controller.py
      dialog.py
    asset_library/
      controller.py
      service.py
      dialog.py
    config.py
    dcc_paths.py
    houdini_asset_bridge.py
    settings/
      controller.py
      dialog.py
    batch_import/
      controller.py
      scanner.py
      file_processor.py
      service.py
      pdg.py
      dialog.py
    nuke_archive/
      service.py
      controller.py
      dialog.py
      cli.py
    houdini_archive/
      service.py
      runner.py
      houdini_worker.py
      controller.py
      dialog.py
      cli.py
    ocio/
      service.py
      controller.py
      dialog.py
    review_copy/
      service.py
      controller.py
tests/
```

`Prism_chAngE_Prism_Functions.py` 只注册 Prism callback 并转发给各 feature controller。业务逻辑、Qt 界面和 Prism 集成分别放在 feature 内，feature 之间不直接互相导入。

## 配置

插件不再读取或写入根目录 `config.json`。在 Prism 中打开
`Settings > User > chAngE_Prism` 设置本机路径，然后点击 `Save`。
配置由 Prism 自己的用户配置系统持久化，插件更新不会覆盖这些值。

Asset Library 的源列表直接在 `Asset Library` 页签内管理，同样写入 Prism 用户配置，对本机所有项目可见。

| Settings 字段 | 说明 |
|---|---|
| `Server Publish Root` | Batch Import 的服务器根目录；无内置默认值，必须由 Settings 设置 |
| `Local Projects Root` | Batch Import 创建或打开本地 Prism 项目的根目录 |
| `Daily Review Destination` | Daily Review Copy 根目录，实际目标为 `<root>/YYYY-MM-DD/` |
| `Hython (from Prism)` | 只读；由 `Settings > User > Apps > Houdini` 的 executable override 自动推导 |
| `PDG Template HIP` | Batch Import 后台 PDG 使用的模板 HIP |
| `Houdini Package Directory` | 包含 Houdini package JSON 的目录，启动 PDG 时作为 `HOUDINI_PACKAGE_DIR` |
| `Current Project OCIO` | 当前 Prism 项目的 OCIO config 覆盖；空值时按 `OCIO` 环境变量、`ocio://default` 回退 |

Batch Import 窗口中修改服务器或本地项目路径时，也会即时写入同一份
Prism 用户设置。旧版根目录 `config.json` 不再参与运行，可在确认新设置后手动删除。

插件目录需要位于 Prism 的 `PRISM_PLUGIN_PATHS` 搜索范围内。

## Asset Library

- 使用 `Add Source` 登记任意外部目录；根节点和子目录保留磁盘上的真实名字。
- 支持 EXR、HDR、JPG/JPEG、PNG、TIF/TIFF、TGA 和 BMP。
- 左侧目录树控制浏览位置，右侧只显示当前目录的直属图片。
- 非空搜索会搜索所有启用源；同一源内具有相同文件名、大小和修改时间的多分类副本合并显示，并可在详情中选择实际路径。
- 选择目录后点击 `Generate Thumbnails`，只为该目录直属素材生成缺失或过期的缩略图；浏览和刷新只读取已有缓存。生成时总并发最多 4 个，其中 HDR/EXR 最多 2 个。缩略图写入素材旁的 `_thumbs/<原文件名含扩展>.jpg`，移除源不会删除素材或缩略图。
- 工具栏 `Size` 支持 `Small`、`Medium`、`Large`，独立 Prism 与 Houdini 分别记忆选择；切换只改变绘制和网格，不会重建 `_thumbs`。
- Details 左侧显示当前 `Active Location` 的大图预览，并且只读取已有且未过期的 `_thumbs` 缓存；无缓存时不会解码原始 HDR/EXR。
- 在 Houdini 内嵌的 Project Browser 中右键 HDR/EXR，可直接在当前 Object 或 LOP 网络创建原生 Environment Light 或 Solaris Dome Light；其他网络只提示切换到支持的网络，不再弹出目标选择器。
- Houdini 内嵌界面会修正高 DPI 缩略图尺寸并使用更紧凑的网格。
- Houdini 灯光始终使用当前 `Active Location` 的绝对路径，不复制素材、不修改已有灯光，也不自动保存 HIP。

完整说明见 [Asset Library.md](Asset%20Library.md)。

## Batch Import

- 项目下拉列表在后台扫描服务器根目录；切换路径时忽略旧结果，关闭窗口无需等待目录扫描。扫描失败原因显示在项目下拉框的提示中。
- 扫描 `shot_animation`、`cloth_solution`、`hair_solution`，递归识别大小写不敏感的 FBX、ABC、MOV 和 XML。
- Filter 支持完整 `episode/sequence/shot` 行，也支持连续三行 `episode/`、`sequence/`、`shot`。
- `Create shot only` 仅创建或更新 Prism 镜头、Fx/Effects 等部门与任务、预设场景和帧范围；Shotinfo 不写入镜头 metadata。
- 默认模式保留服务器源文件路径，在 `published_ref/v####` 写入标准化 `versioninfo.json`；`Copy to local` 会先复制三个发布 step，再让记录和 PDG 指向本地版本。
- Review MOV 进入 Prism `playblasts` 类型的 `review` media 版本；不同 step 的同名 MOV 会保留并自动加 step 前缀。
- `Run PDG FBX Convert` 只把成功镜头中的 FBX、帧范围、Animation XML 的必要 metadata，以及存在时的 Cloth/Hair XML 路径写入独立的 `%TEMP%\chAngE_Prism\batch_import\pdg\json\change_prism_pdg_<随机>\shot_data.json`，并在导入完成后后台启动一次 `hython + topcook.py`。JSON 路径通过 `SHOT_BUILDER_PDG_JSON` 传入，Hython 结束后保留以便排查；导入摘要会提示 PDG 正在后台运行，结束后由 Qt 主线程弹窗给出耗时、JSON、stdout 和 stderr 路径。
- Hython 始终来自 Prism 当前 Houdini executable override；`topcook.py` 从同一 Houdini 安装目录推导，不再保存 `hython_path` 或 `topcook_path`。
- PDG 明确设置 `SHOT_BUILDER_PDG_JSON` 和 Settings 中的 `HOUDINI_PACKAGE_DIR`，不再要求系统预先配置 `PIPELINE_ROOT`。

完整说明见 [Batch Import.md](Batch%20Import.md)。

## Nuke Archive

打包结构：

```text
<shot>/Archives/Compositing/v0001/
├─ nk/
│  └─ scene_archive_v0001.nk
├─ sequences/
│  └─ <material>/
└─ manifest.json
```

核心行为：

- 仅解析标准 `Read {}` 节点，不依赖 Nuke、Prism 或 Qt。
- 图片序列复制整个源目录；MOV 和单张图片只复制该文件。
- 图片序列按规范化源目录去重，单文件按规范化源文件去重；同名不同源素材目录使用 `_2`、`_3` 后缀。
- 归档 Nuke 的 `Read.file` 改为 `../sequences/...`，Root `project_directory` 使用 Nuke 13 可识别的脚本目录表达式。
- 打包前显示文件数、素材容量和目标磁盘空间。
- Archive 版本仅按 `Task` 独立递增；Department 只用于显示，不参与版本编号。`Archives` 页签按 Application、Task 分组，Version 下拉框默认显示该 Task 的最高版本。
- 旧的 `<shot>/Archives/v####` 和 `<shot>/Archives/<department>/<task>/v####` 结构继续兼容，并按源场景的 Task 显示为任务版本。
- `Open Nuke` 使用 Prism 的 Nuke executable、启动模式和环境配置。
- 每个版本可二次确认后永久删除；删除范围是整个 `v####` Archive 目录。

完整说明见 [Nuke Archive.md](Nuke%20Archive.md)。

## Houdini Archive

- 支持 `.hip`、`.hiplc`、`.hipnc` 和 Houdini 20.5+，优先使用源场景的完全相同 build。
- 打包 ABC、FBX、VDB、OBJ/GEO/PLY/STL、纹理/HDRI、LUT、音频及其序列。
- 所有 File Cache 内部引用和 `.bgeo/.bgeo.sc` 固定跳过并保留原路径。
- USD/Solaris、PDG/TOP 动态依赖首版跳过；未知外部引用会阻止打包。
- 外部 HDA/OTL 会复制，但不自动安装或修改 Houdini 启动环境。
- Archive HIP 直接放在 `<task>/v####` 根目录，依赖改写为 `$HIP/dependencies/...`。
- Prism 右键后无预检或进度窗口；单次 hython 写出归档 HIP 和 `Incomplete` manifest 后退出，普通 Python 再根据 manifest 后台复制，完成或失败时弹窗报告。
- 不执行 `/mnt/nas/...` 到 Windows 盘符的路径映射；当前系统无法访问的 `/mnt/nas` 输入会保留原路径并标记为 `Skipped Missing`，不阻止其他依赖打包。

完整说明见 [Houdini Archive.md](Houdini%20Archive.md)。

## ACES / OCIO Converter

- 输入：带标准 RGB 通道的 EXR 单帧或序列。
- OCIO 优先级：项目手动覆盖 → `OCIO` 环境变量 → `ocio://default`。
- 输出：H.264 MP4、ProRes 422 HQ MOV，写入 BT.709 标签。
- Prism 管理媒体沿用原生转换输出路径；外部 EXR 在源目录生成 `.rec709` 输出。

完整说明见 [ACES转换器.md](ACES转换器.md)。

## Daily Review Copy

- 文件右键复制单个文件或目录。
- Media 预览为序列时复制整个序列目录。
- 目标固定为 `<review_copy.destination_root>/YYYY-MM-DD/`。
- 同名文件覆盖；同名目录合并并覆盖冲突文件，不删除目标中额外文件。
- 批量复制会收集失败项并在结束时统一显示。
- 复制在后台执行，不弹出进度窗口；结束后显示非阻塞结果提示。

## 测试

```powershell
python -m unittest discover -s tests -v
```

Archive 的 Qt 测试需要 Prism 自带的 Qt/PySide 环境。可选 Nuke 13 headless 测试：

```powershell
& "C:\Program Files\Nuke13.2v1\Nuke13.2.exe" --safe -t tests\nuke13_archive_smoke.py
```

Houdini HOM 冒烟测试：

```powershell
& "C:\Program Files\Side Effects Software\Houdini 20.5.684\bin\hython.exe" tests\houdini_archive_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 21.0.792\bin\hython.exe" tests\houdini_archive_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" tests\houdini_archive_smoke.py

& "C:\Program Files\Side Effects Software\Houdini 20.5.684\bin\hython.exe" tests\houdini_asset_library_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 21.0.792\bin\hython.exe" tests\houdini_asset_library_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" tests\houdini_asset_library_smoke.py
```

headless/HOM 测试需要对应 DCC 许可证。2026-09-05 在 Prism 2.1.3 / Python 3.13 / PySide6 环境验证：200 项测试中通过 199 项，跳过 1 项目录符号链接测试（环境无法创建链接），包含 bundled OCIO/FFmpeg 转换验证。Houdini 20.5.684、21.0.792 的 Archive 和 Asset Library HOM 冒烟测试均通过；Nuke 13.2v1 和 Houdini 22.0.368 因许可证不可用未完成验证。此记录不代表其他 Prism/DCC 版本或生产场景已经验收。

## 进一步文档

- [开发需求.md](开发需求.md)：需求范围和实现状态
- [Asset Library.md](Asset%20Library.md)：外部图片源、搜索聚合和缩略图规则
- [CLAUDE.md](CLAUDE.md)：代码架构、约定和 Prism API 注意事项
- [prism环境变量.md](prism环境变量.md)：Prism 环境变量速查
- [prism_docs/](prism_docs/)：仓库内 Prism 官方文档镜像
