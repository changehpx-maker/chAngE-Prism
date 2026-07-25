# AGENTS.md

This file provides guidance to coding agents working in this repository. See also [CLAUDE.md](CLAUDE.md) for the full documentation.

## 关键约定

- 遵守 [CLAUDE.md](CLAUDE.md) 中的所有约定
- 修改代码前先读 CLAUDE.md，了解架构和注意事项
- 保持 `Prism_chAngE_Prism_Functions.py` 为薄回调门面；新功能按 `Scripts/change_prism/<feature>/controller.py + service.py + dialog.py` 拆分
- feature 之间不直接互相导入；公共配置和基础设施放在 `Scripts/change_prism/` 根层
- controller 必须懒加载 dialog，避免拖慢 Prism 启动
- context 构造：Prism API 的 context 必须用 `entity.copy()` 展开，不能嵌套 `{"entity": entity}`
- media 版本化用 `identifierType="playblasts"`
- 空值防御：`_increment_version` fallback 到 `lowestVersion + 1`
- 扫描器 `_list_dirs` 有 lru_cache，每次 search 前调 `clear_list_dirs_cache()`
- 失败收集：批量导入失败时收集 shot 路径和异常，结束时展示
