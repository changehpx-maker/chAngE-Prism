### Prism 环境变量参考

Prism 官方文档：`prism_docs/general_environmentVariables.md`

chAngE_Prism 的服务器、本地项目、Daily Review、Batch Import PDG 和当前项目 OCIO 路径
不再使用插件根目录 `config.json`，请在
`Prism Settings > User > chAngE_Prism` 中设置。`PRISM_USER_PREFS`
仍可用于改变 Prism 用户配置文件本身的位置。

Batch Import 的 Hython 不使用 `hython_path` 环境变量或插件 JSON：它由
Prism `Settings > User > Apps > Houdini` 的 executable override 自动推导。
`topcook.py` 同样从该 Houdini 安装目录寻找。PDG 运行时由插件临时设置
`SHOT_BUILDER_PDG_JSON` 和 `HOUDINI_PACKAGE_DIR`，不要求用户设置
`PIPELINE_ROOT`。

**路径/目录**

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PRISM_LIBS` | 无（必填） | Prism 库目录路径 |
| `PRISM_DATA_DIR` | 内置默认 | 覆盖数据目录 |
| `PRISM_USER_PREFS` | 空 | 覆盖用户偏好配置文件路径 |
| `PRISM_PROJECT` | 空 | 启动时自动加载的项目路径 |
| `PRISM_PROJECT_FALLBACK` | 空 | 找不到当前项目时的回退路径 |
| `PRISM_PROJECT_CONFIG_PATH` | 空 | 项目配置文件相对路径 |
| `PRISM_PROJECT_PIPELINE_FOLDER` | `00_Pipeline` | Pipeline 文件夹名称 |
| `PRISM_PROJECT_PRESETS_PATH` | 内置默认 | 项目预设文件目录 |
| `PRISM_DFT_LOCAL_PATH` | 空 | 覆盖本地默认路径 |
| `PRISM_MEDIA_MASTER_LOC` | 空 | 媒体文件主存储位置 |
| `PRISM_PRODUCT_MASTER_LOG` | 空 | 产品文件主存储位置 |

**插件**

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PRISM_PLUGIN_PATHS` | 空 | 额外插件目录（`:` 或 `;` 分隔） |
| `PRISM_PLUGIN_SEARCH_PATHS` | 空 | 插件搜索路径（搜子目录） |
| `PRISM_DEFAULT_PLUGIN_PATH` | 空 | 默认插件路径 |
| `PRISM_FALLBACK_PLUGIN_PATH` | 空 | 备用插件路径 |
| `PRISM_LOAD_PLUGINS_FROM_DFT_PATH` | `1` | 是否从默认路径加载插件 |
| `PRISM_IGNORE_AUTOLOAD_PLUGINS` | 空 | 不自动加载的插件（逗号分隔） |
| `PRISM_LOAD_PRJ_PLUGINS_RECURSIVE` | `0` | 是否递归加载项目插件 |
| `PRISM_ALLOW_HUB_INSTALL` | 空 | 允许自动安装 Hub 插件 |

**UI/行为**

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PRISM_NO_PROJECT_BROWSER` | 空 | 设为 `1` 跳过项目选择窗口 |
| `PRISM_LANGUAGE` | 空 | 设为 `CN` 启用中文界面 |
| `PRISM_AUTOSAVE_INTERVAL` | 空 | 自动保存间隔（分钟） |
| `PRISM_DATE_FORMAT` | 空 | 自定义日期格式 |
| `PRISM_FILE_EXPLORER` | `explorer` | 自定义文件管理器 |
| `PRISM_SKIP_PROJECT_PATH_WARNING` | `0` | 跳过项目路径变更警告 |
| `PRISM_MISSING_MODULES_WARNING` | `1` | 设为 `0` 隐藏缺失模块警告 |
| `PRISM_IGNORE_PATH_LENGTH` | 空 | 设为 `1` 跳过 Windows 路径长度检查 |
| `PRISM_SHOW_INVALID_VERSION_NAMES` | `0` | 显示非法版本名 |
| `PRISM_SHOW_EXR_LAYERS` | 空 | 设为 `0` 隐藏 EXR 图层 |
| `PRISM_DISPLAY_MEDIA_RESOLUTION` | 空 | 设为 `0` 隐藏分辨率信息 |
| `PRISM_USE_DEPARTMENTS_FOR_PRODUCTS` | `1` | 产品浏览器按部门过滤 |
| `PRISM_USE_SEQUENCE_FOLDERS` | 空 | 启用 Sequence 文件夹模式 |
| `PRISM_USE_HARDLINK_MASTER` | 空 | 使用硬链接代替文件复制 |
| `PRISM_COPY_FILE_CONTENT` | `0` | 设为 `1` 复制时连带文件内容 |

**DCC 相关**

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PRISM_NUKE_EXE` | 空 | Nuke 可执行文件路径（预览生成） |
| `PRISM_NUKE_INTERACTIVE_LICENSE` | `0` | 使用 Nuke 交互式许可证 |
| `PRISM_SHOTCAM_DEPARTMENT` | `Layout` | 镜头相机默认部门 |
| `PRISM_SHOTCAM_TASK` | `Cameras` | 镜头相机默认任务 |
| `PRISM_SHOT_INCREMENT` | `10` | 新建镜头递增量 |

**技术/调试**

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PRISM_DEBUG` | `False` | 调试模式（额外日志、热重载模块） |
| `PRISM_PYTHON_VERSION` | `3.13` | Prism 使用的 Python 版本 |
| `PRISM_CONFIG_EXTENSION` | `.json` | 配置文件扩展名 |
| `PRISM_NO_LIBS` | 空 | 设为 `1` 跳过库目录检查 |
| `PRISM_SLIDER_FIX` | `0` | 修复 KDE 等系统的滑块渲染问题 |
| `PRISM_USE_ROBOCOPY` | `1` | Windows 下拷贝文件使用 robocopy |
| `PRISM_REFRESH_OIIO_CACHE` | `False` | 强制刷新 OpenImageIO 缓存 |
| `PRISM_BLACKLISTED_EXTENSIONS` | 空 | 黑名单扩展名，场景文件预设中不显示 |
| `PRISM_ENTITY_THUMBNAIL_EXT` | `.jpg` | 实体缩略图扩展名 |

**运行时内部变量（Prism 自动设置）**

| 变量 | 说明 |
|---|---|
| `PRISM_ROOT` | Prism 安装根目录 |
| `PRISM_VERSION` | Prism 版本号 |
| `PRISM_PROJECT` | 当前项目路径 |
| `PRISM_JOB` | 当前 Job 名称 |
| `PRISM_JOB_LOCAL` | 当前 Job 本地化名称 |
| `PRISM_EPISODE` | 当前剧集名称 |
| `PRISM_USERNAME` | 用户名（可通过 `PRISM_USERNAME` 覆盖） |
| `PRISM_USER_ABBREVIATION` | 用户缩写（可通过 `PRISM_USER_ABBREVIATION` 覆盖） |
