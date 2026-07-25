![[Logo: Substance Painter]](https://prism-pipeline.com/docs/latest/_static/banner_logos/substancepainter_logo.png)

## Substance Painter

This plugin integrates Prism into [Adobe Substance 3D Painter](https://www.adobe.com/products/substance3d-painter.html).

## Overview

This integration enables users to import geometry files into Substance Painter, save and version their scenefiles and export textures to the Prism project folder.

## Setup

This plugin can be installed using the Prism Hub like any other plugin.

When the plugin is loaded, the Prism integration needs to be added to the Substance Painter user settings folder.

In the Prism User Settings in the "DCC apps" -> "Substance Painter", the integration can be added.

Alternatively it can also be added in the Prism installer or by using the setup.bat in the Prism install directory.

The integration should be added to the Substance Painter user preferences, which is here by default: `%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter`.

This folder gets created when you launch Substance Painter for the first time.

Once this is done you can launch Substance Painter and in the "Python" menu click the "PrismInit" option.

This step is needed only once.

Now there is a menu with the Prism icon in the menu bar from where you can access the Prism tools.

![../../_images/substancepainter_menu.jpg](https://prism-pipeline.com/docs/latest/_images/substancepainter_menu.jpg)

## Importing Geometry

To import geometry from your Prism project into Substance Painter you can use the "Import Geometry" option from the Prism menu or rightclick a product version in the Project Browser and select "Import".

![../../_images/substancepainter_import.jpg](https://prism-pipeline.com/docs/latest/_images/substancepainter_import.jpg)

## Saving Scenefiles

You can save new scenefile versions using the options in the Prism menu or by opening the Project Browser and selecting "Create new version from current" in the context menu in the "Scenefiles" tab.

![../../_images/substancepainter_saveVersions.jpg](https://prism-pipeline.com/docs/latest/_images/substancepainter_saveVersions.jpg)

## Exporting Textures

To export texture maps select the "Export Textures" option in the Prism menu.

This will open an export window where you can configure which maps to export.

You can also use export presets, which you can edit in the native Substance Painter Output Template window.

![../../_images/substancepainter_exportTextures.jpg](https://prism-pipeline.com/docs/latest/_images/substancepainter_exportTextures.jpg)

The exported textures are then visible in the "Libraries" tab in the Project Browser.

To see this tab make sure you have the [Libraries Plugin](https://prism-pipeline.com/docs/latest/plugins/Libraries/#plugin-libraries) installed.

![../../_images/substancepainter_viewInLibraries.jpg](https://prism-pipeline.com/docs/latest/_images/substancepainter_viewInLibraries.jpg)

## Scene Building

Access

Result

An initial scenefile "v0001" with the comment "Scene Building" has been created. During the building process, all configured steps - such as "Import Mesh" - will be applied.

Scene Building Settings

Available steps can be configured in the Project Settings:

`Prism Settings > Project > Scene Building > Substance Painter`

![[Scene Building - Substance Painter Settings]](https://prism-pipeline.com/docs/latest/_static/plugins/substance-painter/SubstancePainter_SceneBuilding_Settings.png)

Substance Painter Steps

The following Scene Building steps and their respective settings are available in Substance Painter:

| Import Mesh: |  |
| --- | --- |
| Description: | Available products are imported.  If several products are available, only the first product found will be imported. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |

Recommended Texturing Workflow

By default, all Modeling products are automatically tagged with "to\_surf". This ensures that when the Surfacing department builds a scene, Modeling products are imported.

With a referencing workflow, Modeling products are typically provided in ".hip" or ".ma" file formats. This keeps the asset up to date while materials are created and assigned.

For texture painting, the Surfacing department has an additional "Texturing" task. However, a Modeling product in ".hip" or ".ma" format cannot be imported into Substance Painter due to unsupported file formats. Even if Modeling exports a second product (e.g., in ".abc" format), it still will not work - both products share the "to\_surf" tag.

To exclusively tag a product for Substance Painter the Task Tag (to\_texturing) can be used instead of the Department Tag (to\_surf). And since tasks are always considered first, the "to\_texturing" tag will ensure that Substance Painter imports the correct product.

Further Reading

*Alongside the Substance Painter specific information, additional details on Scene Building can be found on the [Scene Building](https://prism-pipeline.com/docs/latest/general/scene-building) page.*

## Adding Prism integration using environment variables

It is possible to use environment variables to add the Prism integration to Substance Painter instead of adding the Prism integration into the Substance Painter User Preferences.

The following environment variables need to be defined:

```
PRISM_ROOT = C:\Program Files\Prism2
SUBSTANCE_PAINTER_PLUGINS_PATH = C:\ProgramData\Prism2\plugins\SubstancePainter\Integration
```

These environment variables can be set in the system settings.

To load the Prism Substance Painter plugin from a central location in your studio you can set the [SUBSTANCE\_PAINTER\_PLUGINS\_PATH](https://helpx.adobe.com/substance-3d-painter/pipeline-and-integration/configuration/environment-variables.html) environment variable and point it to a folder on your network storage.

In that folder create a `plugins/PrismInit.py` file with the following content:

```
import os
import sys

os.environ["PRISM_ROOT"] = "C:\\Program Files\\Prism2"

def start_plugin():
    prismInit()

def close_plugin():
    global pcore
    if pcore.appPlugin:
        pcore.appPlugin.unregister()

def prismInit():
    prismRoot = os.getenv("PRISM_ROOT")
    scriptDir = os.path.join(prismRoot, "Scripts")

    if scriptDir not in sys.path:
        sys.path.append(scriptDir)

    import PrismCore
    import importlib
    importlib.reload(PrismCore)
    global pcore
    pcore = PrismCore.PrismCore(app="SubstancePainter")
    return pcore
```