## Scene Building

2026-04-17

5 min read

## Overview

"Scene Building" is a tool in Prism that is designed to automatically build the initial scene.

This involves various steps such as applying the frame range, importing available products or media files, and creating the first scene file.

Each step performed by the tool can be enabled or disabled based on entity, department, and task, allowing for a customizable setup.

Additional settings are available for supported plugins or supported workflows (Alembic/USD).

Currently supported plugins for Scene Building are:

- [Blender](https://prism-pipeline.com/docs/plugins/Blender/#scene-building-in-blender)
- [Houdini](https://prism-pipeline.com/docs/plugins/Houdini/#scene-building-in-houdini)
- [Maya](https://prism-pipeline.com/docs/plugins/maya/#scene-building-in-maya)
- [Nuke](https://prism-pipeline.com/docs/plugins/Nuke/#scene-building-in-nuke)
- [Substance Painter](https://prism-pipeline.com/docs/plugins/Substance%20Painter/#scene-building-in-substance-painter)

Behind the scenes, the Scene Building tool uses a configurable Tag System to precisely control the import of products.

## Available Steps

Each step performed by the Scene Building tool is customizable and can be defined based on:

- **Entity** (e.g., Characters, Environments, Sequences, Shots)
- **Department** (e.g., Modeling, Animation, Lighting)
- **Task** (e.g., Texturing, Animation, Compositing)

Scene Building Settings

Available steps can be configured for each supported DCC in the Project Settings:

`Prism Settings > Project > Scene Building`

![[Scene Building - Settings]](https://prism-pipeline.com/docs/_static/general/scene-building/SceneBuilding_Settings.png)

Scene Building Steps

Most Scene Building steps are available across all supported DCCs, though some offer additional steps or settings. Click on a DCC below to see its full list of available steps and settings.

- [Blender](https://prism-pipeline.com/docs/plugins/Blender/#scene-building-in-blender)
- [Houdini](https://prism-pipeline.com/docs/plugins/Houdini/#scene-building-in-houdini)
- [Maya](https://prism-pipeline.com/docs/plugins/maya/#scene-building-in-maya)
- [Nuke](https://prism-pipeline.com/docs/plugins/Nuke/#scene-building-in-nuke)
- [Substance Painter](https://prism-pipeline.com/docs/plugins/Substance%20Painter/#scene-building-in-substance-painter)

## Tag System

The Tag System enables Prism to identify which products each department will import during the scene building process.

Default Product Tags:

Default "Product Tags" can be managed in the Scene Building settings:

`Prism Settings > Project > General > Product Tags > Manage Product Tags`

![[Scene Building - Product Tags]](https://prism-pipeline.com/docs/_static/general/scene-building/SceneBuilding_ProductTags.png)

These tags are then applied automatically for all matching products.

Available Tags:

**Department Tags** (e.g., "to\_surf", "to\_lgt", "to\_anm") are intended for general use.

As an example, if a Modeling export should be included into the scene building of the Surfacing department, the "to\_surf" tag need to be set on the Modeling product.

If additional departments are created via `Prism Settings > Project > Departments`, such as "Research (rnd)" the corresponding tag would be "to\_rnd".

**Task Tags** (e.g., "to\_modeling", "to\_rigging", "to\_lighting") are intended for more specific use cases.

For example, if a department has multiple tasks and the exported product should only be available for import in a specific task.

This can be useful, for example, when building scenes in Substance Painter if a specific export is to be used for texturing. For further reading see [Substance Painter](https://prism-pipeline.com/docs/plugins/Substance%20Painter/#scene-building-in-substance-painter).

If additional tasks are created such as "Texturing" the corresponding tag would be "to\_texturing".

**Special Tags** (e.g., "static", "animated", "usd") are meant to be used for advanced workflows.

The "usd" tag ensures that the product is a valid USD product.

The "static" and "animated" tags are used to automate the Alembic-Workflow. It can be used to automatically import a "static" tagged product and apply the animation from an "animated" tagged product.

For further reading see [Maya-Alembic Referencing Workflow](https://prism-pipeline.com/docs/plugins/maya/alembic-workflow/).

Add Tags:

Besides the default tags, tags can be added or changed in the Project Browser:

`Project Browser > Products tab > Products > Right-click any Product > Edit Tags...`

![[Scene Building - Edit Product Tags]](https://prism-pipeline.com/docs/_static/general/scene-building/SceneBuilding_EditProductTags.png)

In addition, default tags can always be overridden in the respective DCC export settings:

`Export > General > Productname > change`