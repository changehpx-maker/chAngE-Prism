# chAngE_Prism

`chAngE_Prism v2.2.0` 是基于 Prism 2 的制作流程扩展插件，当前主要服务于镜头批量创建、审片媒体、ACES/OCIO 转换以及 Nuke/Houdini Archive 打包。

Windows Prism 2.1.2/2.1.3 是当前正式验证环境。Nuke Archive 纯核心额外兼容 Nuke 13.2 的 Python 3.7；Houdini Archive 支持 Houdini 20.5+。

## 当前功能

| 功能 | Prism 入口 | 用途 |
|---|---|---|
| Batch Import | `chAngE > Batch Import from Server...` | 从服务器发布目录扫描镜头，创建或更新 Prism 项目、镜头、部门、帧范围和 review MOV |
| ACES / OCIO Converter | `chAngE > ACES / OCIO Media Converter...`；Media 右键快速转换 | 将 RGB EXR 单帧/序列转换为 H.264 MP4 或 ProRes MOV |
| Archives | Project Browser 的 `Archives` 页签 | 统一浏览、打开、检查和删除 Nuke/Houdini Archive |
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
    config.py
    batch_import/
      controller.py
      scanner.py
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

首次使用时，将 `config.example.json` 复制为插件根目录下的
`config.json`。`config.json` 保存本机路径并已加入 `.gitignore`：

```json
{
  "server_root": "",
  "local_projects_root": "",
  "review_copy": {
    "destination_root": ""
  }
}
```

| 配置 | 说明 |
|---|---|
| `server_root` | Batch Import 的服务器根目录；空值在 Windows 回退到 `P:\` |
| `local_projects_root` | Batch Import 创建或打开本地 Prism 项目的根目录 |
| `review_copy.destination_root` | Daily Review Copy 根目录，实际目标为 `<root>/YYYY-MM-DD/` |
| `ocio_converter.project_overrides` | 按 Prism 项目保存的 OCIO config 覆盖，由转换器界面维护 |

插件目录需要位于 Prism 的 `PRISM_PLUGIN_PATHS` 搜索范围内。

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
& "C:\Program Files\Side Effects Software\Houdini 21.0.631\bin\hython.exe" tests\houdini_archive_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" tests\houdini_archive_smoke.py
```

headless/HOM 测试需要对应 DCC 许可证。最近一次 Prism PySide6 环境验证共发现 85 项测试，通过 79 项、跳过 6 项环境测试；Houdini 20.5.684、21.0.631、22.0.368 的 HOM 冒烟测试此前均已通过。

## 进一步文档

- [开发需求.md](开发需求.md)：需求范围和实现状态
- [CLAUDE.md](CLAUDE.md)：代码架构、约定和 Prism API 注意事项
- [prism环境变量.md](prism环境变量.md)：Prism 环境变量速查
- [prism_docs/](prism_docs/)：仓库内 Prism 官方文档镜像
