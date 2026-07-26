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
- 操作：双击或右键可打开文件、在 Explorer 中定位、复制路径。

同一源中，如果多个文件具有相同的文件名、文件大小和纳秒修改时间，全库搜索会将它们合为一张卡片。详情区的 `Active Location` 可以在所有分类路径之间切换。不同源之间不会合并。

## 缩略图

选择左侧文件夹后，点击 `Generate Thumbnails` 才会为该文件夹中的直属图片生成缩略图。已有且未过期的缩略图会直接跳过；源文件更新后，旧缩略图会重新生成。HDR/EXR 通过 Prism Media API 解码。

浏览、搜索、排序和 `Refresh` 只读取已有缩略图，不会触发新的缩略图生成。生成任务使用受控后台并发：总并发最多 4 个，其中 HDR/EXR 最多 2 个，普通图片可以使用其余槽位。这样可以提高批量速度，同时限制大型 HDR/EXR 的内存峰值。为避免同名格式冲突，缓存路径包含原始扩展名：

```text
<素材目录>\_thumbs\<原文件名含扩展>.jpg
```

例如：

```text
clear\_thumbs\studio_4k.exr.jpg
```

源图片更新后旧缩略图会自动重建。如果目录不可写，当前会话仍会显示内存预览，但无法持久缓存。

## 当前边界

首版不包含：

- Houdini、Nuke、Maya 等 DCC 导入或节点创建
- 在线 Poly Haven 下载
- 标签、收藏或持久数据库
- 文件系统实时监听
- 素材复制、移动、重命名或删除

需要刷新文件系统变化时，点击 `Refresh`。
