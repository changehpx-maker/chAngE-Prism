# ACES / OCIO Media Converter

`chAngE_Prism v2.2.0` 内置免费的 ACES/OCIO 视频转换器。它使用 Prism 自带的 OpenImageIO 和 FFmpeg，不依赖 Media Extension。

## 使用方法

有两个入口：

1. Project Browser 菜单：`chAngE > ACES / OCIO Media Converter...`，打开完整队列和色彩设置窗口
2. Media 页预览区域右键：`ACES / OCIO Quick Convert`，直接选择 `H.264 MP4`、`ProRes 422 HQ MOV` 或 `MP4 + MOV`，不打开转换窗口

右键快速转换自动载入当前 EXR 序列，并使用当前项目保存的 OCIO 设置和项目 FPS。需要更改 Input/Display/View、测试帧或处理多个序列时，使用 `chAngE` 菜单的完整窗口。工具会扫描同目录、归并序列并检查缺帧。

## 色彩设置

OCIO config 按以下顺序选择：

1. 当前 Prism 项目保存的手动覆盖
2. Prism 进程的 `OCIO` 环境变量
3. OpenImageIO 自带的 `ocio://default`

建议选择与 Houdini、Nuke 渲染/合成完全相同的 `.ocio` 文件。使用默认配置时工具会显示黄色警告。

标准 ACES 审片设置：

```text
Input Colorspace: ACEScg
Display:          Rec.1886 Rec.709 - Display
View:             ACES SDR View（名称取决于 ACES config 版本）
```

开始整段转换前，可以选择队列项目并点击 `Test Frame` 检查中间帧。

## 输出

- H.264 MP4：CRF 18、yuv420p、limited range、faststart
- ProRes MOV：ProRes 422 HQ、yuv422p10le、limited range；默认使用快速的 `prores_aw`
- 完整窗口可以将 MOV encoder 切换为 `Compatibility (prores_ks)`；右键快速转换固定使用默认 Fast 模式
- 两种输出都写入 BT.709 primaries、transfer 和 matrix 标签
- FPS 默认读取 Prism 项目设置，也可以在窗口中覆盖
- 奇数分辨率会在右侧或底部补齐一像素
- MOV 使用 10-bit DPX 中间帧，MP4-only 使用 8-bit 无压缩 TIFF；两种格式仍复用一次 OCIO 转换结果

Prism 管理的媒体完全沿用 Prism 自带 Convert 的输出规则：

```text
PRISM_MEDIA_CONVERSION_OUTPUT_MODE=same_folder    # 默认
PRISM_MEDIA_CONVERSION_OUTPUT_MODE=version_suffix
PRISM_MEDIA_CONVERSION_OUTPUT_MODE=next_version
```

外部 EXR 写在源目录，文件名增加 `.rec709`，例如：

```text
shot.beauty.1001.exr -> shot.beauty.rec709.mp4
```

已有输出会统一询问 `Replace All`、`Skip Existing` 或取消。正式文件只在编码成功并通过首帧解码验证后提交。

## 当前限制

- 仅支持包含标准 `R/G/B` 通道的 EXR 单帧和序列
- 输出视频不保留 Alpha，不处理音频
- 缺帧序列不会自动跳帧或补帧
- Windows Prism 2.1.2/2.1.3 已验证；Linux/macOS 只提供工具查找兼容分支

## 验证

```powershell
python -m unittest discover -s tests -v

$env:PRISM_TEST_ROOT = "D:\pipeline\Prism\Prism_v2.1.3"
python -m unittest tests.test_ocio_integration -v
```
