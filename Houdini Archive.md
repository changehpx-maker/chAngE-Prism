# Houdini Archive

Houdini Archive 用于把单个 Houdini 场景和首版支持的外部输入打包到镜头级 Archive。匹配版本的 `hython` 只启动一次，负责依赖扫描、内存参数重写、Archive Save As 和初始 manifest；它退出后由普通 Python 根据 manifest 复制文件并写入最终结果。核心服务和 CLI 不依赖 Prism，但运行时必须有可用的 Houdini 20.5+。

## Prism 使用方式

1. 在 Project Browser 的 Scenefiles 中选中镜头下的 `.hip`、`.hiplc` 或 `.hipnc`。
2. 右键选择 `Package Houdini Archive...`。
3. 打包在后台直接执行，不显示预检或进度窗口。
4. 完成后弹窗显示 Archive 路径、状态、文件数、容量和跳过项；失败时显示原因。
5. 在 `Archives` 页签按 Task 查看 Nuke 与 Houdini Archive。

同一个源 HIP 正在打包时不会重复提交。Prism 模式的大文件复制不占用 Houdini 许可证：`hython` 写出归档 HIP 和 `Incomplete` manifest 后立即退出，复制阶段只使用 Python 标准库。

`Archives` 页签支持：

- Nuke/Houdini 图标、Application、Department、Task、版本、归档场景、源场景、创建信息和健康状态。
- 同一 Application、Task 的多次 Archive 合并为一行；Department 只显示当前版本所属部门，不参与版本编号。
- 根据当前行显示 `Open Nuke` 或 `Open Houdini`，并统一通过 Prism `core.openFile()` 启动。
- Houdini 版本、FPS、帧范围、依赖数、跳过缓存数、HDA 数和容量详情。
- Node、Parameter、Original、Archive Path、Classification、Status 依赖表。
- 每行永久删除按钮和二次确认；`.incomplete` 版本禁止删除。

## 输出结构

```text
<shot>/Archives/Effects/v0001/
├─ SC01-shot0510_Effects_v0007_archive_v0001.hip
├─ dependencies/
│  ├─ alembic/
│  ├─ fbx/
│  ├─ volumes/
│  ├─ geometry/
│  ├─ textures/
│  ├─ lut/
│  ├─ audio/
│  └─ hda/
├─ logs/
│  └─ hython.log
└─ manifest.json
```

`.hiplc` 和 `.hipnc` 保留原许可证扩展名。版本仅按 `Task` 独立递增，Department 不参与编号；manifest 的 `application` 字段用于区分 DCC。旧的 `<shot>/Archives/v####` 和 `<shot>/Archives/<department>/<task>/v####` 结构继续扫描；缺少 `application` 的旧 manifest 按 Nuke 处理，并从源场景路径推导 Department/Task。

新 Houdini Archive 的 HIP 直接位于版本根目录，并使用 `$HIP/dependencies/...`。旧版 `hip/` 子目录结构继续兼容；不要手动把旧 HIP 移到根目录，因为旧场景中的 `$HIP/../dependencies/...` 会随位置变化而断链。

## Houdini 版本选择

工具从 HIP 二进制头读取 `_HIP_SAVEVERSION`：

1. 优先选择完全相同的 Houdini build。
2. 没有相同 build 时，只允许同一 major/minor 下不低于源 build 的最低已安装版本，并显示警告。
3. 只有更低 build 或不同 major/minor 时打包失败。

Prism 模式先检查 Houdini executable override，并推导同目录的 `hython.exe`。override 不兼容时扫描本机 SideFX Houdini 安装。Worker 继承 Prism `startEnv`、Houdini 用户环境、项目环境和 `preLaunchApp` 对环境的修改。

Archive 场景的打开仍交给 Prism，因此沿用 Prism 的 Houdini executable override 和项目环境。

## 依赖分类

分类顺序固定为：

1. `Internal`
   - `op:`、`opdef:`、`oplib:` 等内部引用。
   - `$HFS`、`$HH` 下的 Houdini 内置脚本和资源。
   - 不复制、不改写、不算缺失。
2. `Output`
   - Driver/ROP 输出、渲染输出、Configure Layer 保存路径等。
   - 不复制、不改写、不算缺失。
3. `Skipped Cache`
   - 当前节点或任意祖先是 File Cache。
   - 所有 `.bgeo`、`.bgeo.sc`。
   - 路径保持原样，不计容量，缺失也不阻止打包。
4. `Skipped Unsupported`
   - Solaris/USD 与 PDG/TOP 动态依赖。
   - 路径保持原样，并使健康状态显示 `Complete with Exclusions`。
5. `Skipped Missing`
   - 当前系统无法访问的 `/mnt/nas/...` 输入。
   - 不做 Windows 盘符映射，不复制、不改写；manifest 保留节点、参数、原路径及缺失原因。
   - 不阻止其他依赖打包，并使健康状态显示 `Complete with Exclusions`。
6. `Package Input`
   - Alembic、FBX、非 File Cache VDB、OBJ、GEO/GEO.GZ、PLY、STL。
   - EXR、HDR、PNG、JPG/JPEG、TIF/TIFF、TX、TGA。
   - CUBE、LUT、3DL。
   - WAV、AIF/AIFF、MP3。
7. `Unsupported`
   - 其他无法确认用途的外部引用会使本次打包失败，并在结果弹窗中显示。

`.abc` 文件名包含 `cache` 不影响分类。File Cache/BGeo 是按节点与扩展名判断，不按普通文件名关键词判断。

## 序列、复制与重写

支持 `$F`、`$F4`、`${F4}`、`####`、`%04d` 和 `<UDIM>`：

- 单文件只复制该文件。
- 帧序列和 UDIM 只复制匹配同一模式的文件，不复制整个目录。
- 序列复制所有匹配文件，不限制播放帧范围。
- 单文件按规范化源文件去重；序列按规范化源目录和文件模式共同去重。
- 同名不同源的素材目录依次追加 `_2`、`_3`。
- 大文件由普通 Python 分块复制；Prism 中不显示进度窗口。

仅 `Package Input` 改写为：

```text
$HIP/dependencies/<category>/<material>/<filename-or-pattern>
```

锁定参数、会解析成多个不同源模式的关键帧/动态路径，以及无法安全冻结的表达式都会阻止打包。源 HIP、File Cache、BGeo、输出、USD/PDG 和内部引用永远不修改。

## HDA

- Embedded 和 `$HFS/$HH` 下的内置 HDA 不复制。
- 外部 `.hda/.otl` 按源文件去重，复制到 `dependencies/hda/`。
- 不修改 `HOUDINI_OTLSCAN_PATH`，不自动 install，也不嵌入 HIP。
- manifest 写入 `activation: "manual"`；目标环境需要手动安装。
- 外部 HDA 缺失或不可读时本次打包失败。

## 事务与健康状态

Prism 打包使用单次 `hython` Worker：

1. 排他创建新的 `v####` 和 `.incomplete`。
2. Worker 加载源 HIP，收集依赖并生成复制任务。
3. Worker 只在内存中改写 `Package Input`，直接 Save As 到 Archive。
4. Worker 写入状态为 `Incomplete` 的 manifest 后退出。
5. 普通 Python 从 manifest 读取源文件清单，复制依赖和 HDA。
6. 按源/目标文件大小验证复制结果，原子更新最终 manifest 并删除 `.incomplete`。

源 HIP 的磁盘内容不会修改。由于不再启动第二次 `hython`，Prism 后台流程不执行归档 HIP 重开验证；Archive 健康检查改为依据 manifest、归档场景文件和复制结果。失败会清理本次新版本，不影响已有 Archive。

健康状态优先级：

1. `Incomplete`
2. `Invalid Manifest`
3. `Missing Files`
4. `Source Changed`
5. `Complete with Exclusions`
6. `Complete`

## 独立 CLI

将插件 `Scripts` 加入 `PYTHONPATH`：

```powershell
$env:PYTHONPATH = "D:\pipeline\pkgs\prism\chAngE_Prism\Scripts"
python -m change_prism.houdini_archive.cli SOURCE_HIP --archive-root PATH
python -m change_prism.houdini_archive.cli SOURCE_HIP --archive-root PATH --hython PATH --yes
```

默认打印预检摘要并询问确认，`--yes` 跳过确认。退出码：

- `0`：成功。
- `1`：预检或执行失败。
- `2`：用户取消。

公共接口：

```python
from change_prism.houdini_archive.service import (
    build_package_plan,
    execute_background_package,
    execute_package,
)

plan = build_package_plan(
    source_hip,
    archive_root,
    hython_executable=None,
    worker_env=None,
)
result = execute_package(plan)

# Prism 使用：无人工预检、单次 hython、随后按 manifest 复制
result = execute_background_package(
    source_hip,
    archive_root,
    hython_executable=None,
    worker_env=None,
)
```

`build_package_plan()` 和 `execute_package()` 保留给独立 CLI 的预检确认流程。Prism UI 使用 `execute_background_package()`。

## 测试

默认单元测试不需要 Houdini 许可证：

```powershell
python -m unittest discover -s tests -v
```

HOM 冒烟测试使用临时小素材，不写真实镜头：

```powershell
& "C:\Program Files\Side Effects Software\Houdini 20.5.684\bin\hython.exe" tests\houdini_archive_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 21.0.631\bin\hython.exe" tests\houdini_archive_smoke.py
& "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" tests\houdini_archive_smoke.py
```

需要有效的 Houdini Batch/FX 许可证。

提供的 `SC01-shot0510_Effects_v0007.hip` 只做只读扫描验收：当前文件识别为 Houdini 21.0.631、25 FPS、帧范围 101–790、77 条引用；File Cache/BGeo 均被跳过，当前系统无法访问的 `/mnt/nas/...` 输入标记为 `Skipped Missing` 并保留原路径，不阻止其他依赖打包。自动测试不会对该镜头创建 Archive。
