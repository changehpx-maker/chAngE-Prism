# Asset Library

`Asset Library` 是 chAngE_Prism 的外部图片素材浏览器。它只登记并扫描用户选择的目录，不会把素材复制到 Prism 项目。

## 入口

打开 Prism Project Browser，切换到 `Asset Library` 页签。页签外壳会随 Project Browser 创建，完整界面和目录扫描只在首次进入时加载。

## 添加和管理源

1. 点击 `Add Source`。
2. 选择需要管理的目录，例如：

   ```text
   D:\pipeline\PolyHaven\polyhaven_hdris\categories
   ```

3. 左侧根节点使用真实目录名，因此该路径显示为 `categories`。
4. 展开目录树并选择分类。右侧只显示当前目录的直属图片，不递归混入子目录内容。

源列表保存在 Prism 用户配置的
`change_prism.asset_library.sources` 中，对本机的所有 Prism 项目生效。

- 取消根节点复选框会停用该源，但保留配置。
- 不可访问的源显示为 `Offline`，不会被自动移除。
- `Remove` 只取消登记，不删除素材或已经生成的 `_thumbs`。
- 同一路径不能重复添加；Windows 路径比较不区分大小写。

## 支持格式

- HDR/VFX：EXR、HDR
- 常用图片：JPG/JPEG、PNG、TIF/TIFF、TGA、BMP

扩展名匹配不区分大小写。扫描会跳过 `_thumbs`，也不会跟随符号链接或目录联接。

## 浏览和搜索

- 空搜索：右侧只显示左侧当前目录中的直属图片。
- 全库搜索：输入文字后搜索所有启用源，匹配文件名、源目录名和相对目录名。
- 排序：支持名称、修改时间和文件大小，以及升序/降序。
- 显示尺寸：工具栏的 `Size` 可切换 `Small`、`Medium`、`Large`。独立 Prism 与 Houdini 分别记忆自己的选择；切换尺寸只重排界面并复用已有缓存，不会重新生成缩略图。
- 操作：双击或右键可打开文件、在 Explorer 中定位、复制路径。在 Houdini 内嵌的 Project Browser 中，HDR/EXR 右键还可以创建环境光。

同一源中，如果多个文件具有相同的文件名、文件大小和纳秒修改时间，全库搜索会将它们合为一张卡片。详情区的 `Active Location` 可以在所有分类路径之间切换。不同源之间不会合并。详情区左侧会放大显示当前位置已有的 `_thumbs` 缓存；没有有效缓存时显示占位文字，不会为了详情预览读取或解码原始 HDR/EXR。

## Houdini 环境光

该功能只在 Houdini 内嵌的 Prism Project Browser 中显示，不启动 Hython，也不从独立 Prism 连接 Houdini。右键 HDR/EXR 时会使用详情区 `Active Location` 当前选中的真实绝对路径：

- Object 网络创建原生 `envlight`，并设置 `env_map`。
- LOP 网络创建 `domelight::3.0`，并设置 Texture。`/stage` 与 `/obj/lopnet` 都按真实 LOP 类别处理。
- LOP 已有 Display 节点时，新 Dome Light 连接在其后并成为新的 Display 节点；空网络中直接创建。
- 右键菜单打开时已经位于 Object 或 LOP 网络，灯光会直接创建到当前可见 Network Editor 显示的网络；不再弹出目标选择器。
- 当前位于 SOP、MAT、TOP 等不支持的网络时只显示提示，不修改场景。切换到 `/obj` 或进入 `/stage`、`/obj/lopnet` 等 LOP 网络后再次执行即可。

每次操作始终创建新灯光，并作为一次 Houdini Undo 记录。它不会修改已有灯光、复制 HDRI、转换为 `$JOB` 路径或自动保存 HIP。Object 首版只支持原生 Environment Light，不创建 Redshift、Arnold 或 RenderMan 专用节点。

## 缩略图

选择左侧文件夹后，点击 `Generate Thumbnails` 才会为该文件夹中的直属图片生成缩略图。按住 `Ctrl` 或 `Shift` 可以同时选择多个文件夹，按钮会汇总这些文件夹的直属图片并按真实路径去重。右侧网格仍显示最后一个当前文件夹。已有且未过期的缩略图会直接跳过；源文件更新后，旧缩略图会重新生成。HDR/EXR 通过 Prism Media API 解码。

浏览、搜索、排序和 `Refresh` 只读取已有缩略图，不会触发新的缩略图生成。生成任务使用受控后台并发：总并发最多 4 个，其中 HDR/EXR 最多 2 个，普通图片可以使用其余槽位。这样可以提高批量速度，同时限制大型 HDR/EXR 的内存峰值。为避免同名格式冲突，缓存路径包含原始扩展名：

Houdini 的高 DPI 内嵌界面会按实际像素密度显示缩略图，并使用更紧凑的网格间距。`Size` 的选择分别保存在 `change_prism.asset_library.thumbnail_sizes.houdini` 和 `change_prism.asset_library.thumbnail_sizes.standalone`。

```text
<素材目录>\_thumbs\<原文件名含扩展>.jpg
```

例如：

```text
clear\_thumbs\studio_4k.exr.jpg
```

源图片更新后旧缩略图会自动重建。如果目录不可写，当前会话仍会显示内存预览，但无法持久缓存。

## 当前边界

当前不包含：

- 独立 Prism 与已打开 Houdini 之间的 IPC
- Nuke、Maya 等其他 DCC 导入或节点创建
- Renderer 专用灯光或更新已有 Houdini 灯光
- 在线 Poly Haven 下载
- 标签、收藏或持久数据库
- 文件系统实时监听
- 素材复制、移动、重命名或删除

需要刷新文件系统变化时，点击 `Refresh`。
