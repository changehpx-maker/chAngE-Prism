# Batch Import

## 入口与用途

在 Prism Project Browser 中打开：

```text
chAngE > Batch Import from Server...
```

它把服务器发布目录中的镜头初始化到本地 Prism 项目，并可整理发布引用、复制到本地或继续运行后台 PDG FBX Convert。

## 服务器结构

```text
<server>/<project>/publish/shot/<episode>/<sequence>/<shot>/
├─ shot_motion/shot_animation/
│  ├─ fbx/
│  ├─ review/
│  └─ xml/
└─ shot_solution/
   ├─ cloth_solution/
   │  ├─ vfx/
   │  ├─ review/
   │  └─ xml/
   └─ hair_solution/
      ├─ vfx/
      ├─ review/
      └─ xml/
```

扫描器递归并按大小写不敏感方式收集：

| Step | 文件 |
|---|---|
| Animation | FBX、MOV、XML |
| Cloth | ABC、MOV、XML |
| Hair | ABC、MOV、XML |

XML 中的 `render_start_frame` 和 `sequence_frame` 用于设置镜头帧范围；解析失败时新镜头回退到 `1001-1100`。

## Filter

每行一个完整路径：

```text
Q2EP007/SC01/shot001
Q2EP007/SC01/shot002
```

也支持旧制片表格复制出的三行一组：

```text
Q2EP007/
SC01/
shot001
```

点击 `Search Server` 后扫描在后台线程运行，结果表显示 step 和 review 数量。

## 三种导入模式

### Create shot only

只创建或更新 Prism 项目和镜头：

- Prism sequence = 服务器 episode。
- Prism shot = `<sequence>_<shot>`。
- 新镜头创建 Fx/Effects、Lighting/Lighting、Compositing/Compositing。
- 创建匹配 Houdini/Nuke 的预设场景。
- Shotinfo 只更新帧范围，不写入镜头 metadata。

不创建 `published_ref`，不导入 review，不运行 PDG。

### Reference server files

不勾选 `Create shot only` 和 `Copy to local` 时：

- 创建 Prism product `published_ref/v####`。
- `versioninfo.json` 记录服务器 FBX、ABC、XML、MOV 的规范化路径。
- Review MOV 复制到 Prism `review` playblast 版本。
- 源资产仍指向服务器发布目录。

### Copy to local

在 Reference 模式基础上，把 Animation、Cloth、Hair 三个 step 复制到本次
`published_ref/v####`，然后让 `versioninfo.json` 和可选 PDG 指向本地副本。

## PDG FBX Convert

勾选 `Run PDG FBX Convert` 后，Batch Import 完成时：

1. 只把成功镜头中的 FBX、帧范围和脱敏后的必要 XML metadata 写到
   独立的 `%TEMP%\change_prism_pdg_<随机>\shot_data.json`。
2. 从 Prism 当前 Houdini executable override 的同目录推导 `hython.exe`。
3. 从该 Houdini 安装目录推导 `houdini/python*libs/pdgjob/topcook.py`。
4. 后台启动一次 `hython -u topcook.py --hip ... --toppath /obj/topnet`。
5. 完成后弹窗显示退出码及 stdout/stderr 日志。

Hython 和 topcook 不保存为插件配置。运行前在 Prism 中配置：

```text
Settings > User > Apps > Houdini
  Executable override = <Houdini>/bin/houdini.exe

Settings > User > chAngE_Prism
  PDG Template HIP = Convert_assets.hip
  Houdini Package Directory = 包含 package JSON 的目录
```

插件会合并 Prism 的 `startEnv`、Houdini 用户环境、项目环境和
`preLaunchApp` 回调，随后显式设置：

- `SHOT_BUILDER_PDG_JSON`（指向本次运行的独立临时 JSON）
- `HOUDINI_PACKAGE_DIR`

不再读取插件根目录 `config.json`，也不要求系统设置 `PIPELINE_ROOT`。
Hython 结束后会删除本次临时 JSON 和它的随机目录。

日志位于 Prism 用户配置文件旁：

```text
<Prism user prefs folder>/chAngE_Prism/logs/pdg/
```

单镜头导入失败不会中断整个批次。失败列表会在结果窗口显示，并写入同一用户目录下的 `logs/reports/`。
