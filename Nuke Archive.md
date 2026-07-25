# Nuke Archive

Nuke Archive 用于将单个 `.nk` 文件及其标准 Read 依赖打包到镜头目录。纯核心不依赖 Prism、Qt 或 Nuke API，可以在 Python 3.7 / Nuke 13.2 环境独立使用。

## Prism 使用方式

1. 在 Project Browser 的 Scenefiles 中选中镜头下的 `.nk` 文件。
2. 右键选择 `Package Nuke Archive...`。
3. 检查 Read 数、唯一复制项、文件数、素材容量、目标磁盘剩余空间和素材映射。
4. 确认后等待后台复制完成。
5. 在 `Archives` 页签按镜头查看所有 Nuke/Houdini 版本。

`Archives` 页签支持：

- Nuke/Houdini 图标、Application、Department、Task、版本、归档场景、源场景、创建人、时间和健康状态。
- 同一 Application、Task 的多个 Archive 版本合并为一行；Department 只显示当前版本所属部门，不参与版本编号。
- `Open Nuke`：通过 Prism 的 `core.openFile()` 启动，沿用 Prism 的 Nuke executable override、Nuke/NukeX/Studio 模式、用户与项目环境。
- `Open Folder`：打开整个版本目录。
- Version Details：Read/依赖数、复制项、文件数、素材容量、完整路径和映射。
- 每行 `Delete`：二次确认后永久删除整个版本目录；`.incomplete` 版本禁止删除。

## 输出结构

```text
<shot>/Archives/Compositing/v0001/
├─ nk/
│  └─ SC01-shot0500_Compositing_v0005_archive_v0001.nk
├─ sequences/
│  ├─ rnd_env_debris/
│  ├─ rnd_qingxian_part/
│  └─ rnd_qingxian_part_2/
└─ manifest.json
```

每个 `Task` 独立扫描最高 `v####` 并递增，Department 不参与编号。版本目录使用排他创建；复制失败或取消时清理本次新建目录，不覆盖已有版本。旧的 `<shot>/Archives/v####` 和 `<shot>/Archives/<department>/<task>/v####` 结构继续扫描，并按源场景路径推导 Task 后显示为任务版本。

## Read 解析

首版只解析标准 `Read {}`：

- 支持绝对路径、普通相对路径、引号路径和大括号路径。
- 支持 `%04d`、`%d`、`####` 等帧标记。
- 源路径原本为相对路径时，以源 `.nk` 所在目录解析。
- 展开当前进程已经定义的环境变量。
- Tcl/Python 表达式、未定义环境变量、缺失文件或缺失序列目录会导致预检失败。

暂不收集：

- `DeepRead`
- `ReadGeo`
- Precomp / LiveGroup
- 字体、Gizmo、OCIO 和其他插件依赖
- Write 输出

## 复制与路径重写

- 图片序列复制整个源目录，包括其他文件和子目录。
- MOV 或单张图片只复制该文件。
- 图片序列按规范化源目录去重，单文件按规范化源文件去重；多个 Read 引用同一复制源时共用目标素材目录。
- 素材目录名由文件名移除扩展名和帧标记后生成，并清理 Windows 非法字符。
- 不同源路径产生同名素材时依次追加 `_2`、`_3`。
- 仅修改归档副本；源 `.nk`、Write 路径和 Prism 自定义 knob 保持不变。
- Read 改写为 `../sequences/<material>/<original pattern>`，统一使用正斜杠。
- Root `project_directory` 写为 Nuke 保存格式：

```text
project_directory "\[python \{nuke.script_directory()\}]"
```

保留源脚本的 Nuke 版本头，不执行新版脚本向 Nuke 13 的节点降级。

## 容量与健康状态

预检统计去重后实际复制 payload 的文件数和字节数，并读取目标卷剩余空间。空间明确不足时确认按钮不可用，执行前也会再次阻止打包。

健康状态优先级：

1. `Incomplete`：存在 `.incomplete`、缺少 manifest，或 manifest 标记未完成。
2. `Invalid Manifest`：JSON 无法解析或结构不合法。
3. `Missing Files`：归档 Nuke、素材目录或单文件依赖缺失。
4. `Source Changed`：源 Nuke 不存在，或大小/修改时间与打包时记录不同。
5. `Complete`：快速检查通过。

健康检查是快速存在性检查，不逐帧读取内容或计算校验和。新 manifest 记录容量；旧 manifest 在用户选中版本时临时扫描该版本并缓存到当前 UI，不改写旧文件。

## manifest.json

主要字段：

- Archive 版本、源 Nuke、归档 Nuke。
- 创建人和带时区时间。
- Read 节点名、原始路径、解析路径、归档路径和素材目录。
- 每个复制项的源路径、类型、文件数、容量和复制结果。
- Read 数、复制项数、总文件数和总素材容量。
- 源 Nuke 的文件大小和纳秒修改时间，用于 `Source Changed`。

## 删除安全

删除是永久操作，范围为整个 `<shot>/Archives/<task>/v####`；两种旧目录结构仍可按原位置删除：

- UI 显示版本号、完整路径和不可恢复提示。
- 服务层要求目标是当前版本父目录的直接 `v####` 子目录。
- 同时校验规范化路径和真实路径，拒绝路径逃逸。
- 带 `.incomplete` 的版本禁止从浏览器删除。
- 删除成功后立即刷新列表。

## 独立 CLI

将插件的 `Scripts` 加入 `PYTHONPATH`：

```powershell
$env:PYTHONPATH = "D:\pipeline\pkgs\prism\chAngE_Prism\Scripts"
python -m change_prism.nuke_archive.cli SOURCE_NK --archive-root PATH
```

CLI 默认显示预检并要求确认。自动化使用：

```powershell
python -m change_prism.nuke_archive.cli SOURCE_NK --archive-root PATH --yes
```

核心接口：

```python
from change_prism.nuke_archive.service import (
    build_package_plan,
    execute_package,
)

plan = build_package_plan(source_nk, archive_root)
result = execute_package(plan)
```

## 兼容性与测试

- 核心和 CLI：Python 3.7 标准库，不导入 Prism、Qt 或 Nuke。
- Prism UI：`qtpy`，保持 Qt5 / PySide2 写法。
- 可选 Nuke 13 测试：

```powershell
& "C:\Program Files\Nuke13.2v1\Nuke13.2.exe" --safe -t tests\nuke13_archive_smoke.py
```

该测试会在临时目录生成小型素材，打开、保存并重开归档脚本，不写入真实镜头；需要有效 Nuke 许可证。
