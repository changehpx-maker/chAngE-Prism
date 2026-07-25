![[Logo: Houdini]](https://prism-pipeline.com/docs/latest/_static/banner_logos/houdini_logo.png)

## Houdini

This plugin integrates Prism into [SideFX Houdini](https://www.sidefx.com/products/houdini).

Supported versions: 18.5+ (Python 3)

## Guides

The following section introduces the Prism-Houdini integration, covering the Basics as well as advanced USD workflows.

![[Thumbnail: Houdini - Basics]](https://prism-pipeline.com/docs/latest/_images/Houdini_Basics_thumbnail.jpg) [Basics](https://prism-pipeline.com/docs/latest/guides/houdini/basics/#houdini-basics)

![[Thumbnail: Houdini - USD]](https://prism-pipeline.com/docs/latest/_images/Houdini_USD_thumbnail.jpg) [USD](https://prism-pipeline.com/docs/latest/guides/houdini/usd/#houdini-usd)

## Setup

The plugin can be installed from the Prism Hub. After the plugin is installed, the Prism integration needs to be added to the Houdini preferences folder. This can be done in the Prism User Settings -> "DCCs apps".

This is the path, which should be selected for the integration (with different version numbers possible): `%USERPROFILE%\Documents\houdini20.5`

## Accessing Prism in Houdini

Prism is available inside Houdini from the "Prism" menu in the main menu bar.

![../../_images/houdini_menu.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_menu.jpg)
- save and version up your scene
- save, version up your scene and add a description/thumbnail
- open the Project Browser
- open the State Manager to import, export, playblast and render files
- open the Prism Settings

Additionally there is a Prism Filecache SOP HDA and a Prism ImportFile SOP HDA to import and export data from the nodegraph.

## Saving Scenefiles

You can save new scenefile versions using the options in the Prism menu or by opening the Project Browser and selecting "Create new version from current" in the context menu in the "Scenefiles" tab.

![../../_images/houdini_saveVersions.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_saveVersions.jpg)

## Importing Objects

To import objects from your Prism project into Houdini you can use the Prism ImportFile SOP HDA.

![../../_images/houdini_import_sop.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_import_sop.jpg)

Alternatively you can import files by opening the State Manager from the Prism menu, expanding the "Import" section and clicking the "Import" button.

The Product Browser will open where you can select and import a product version by double clicking it.

Another alternative is to rightclick a product version in the Project Browser and select "Import".

![../../_images/houdini_import.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_import.jpg)

## Exporting Objects

To export objects from Houdini into your Prism project you can use the Prism Filecache SOP HDA.

![../../_images/houdini_export_sop.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_export_sop.jpg)

Alternatively you can open the State Manager from the Prism menu and click the "Export" button in the "Export" section.

This will create an export state where you can set your export settings and define which objects to export.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and export your objects.

![../../_images/houdini_export.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_export.jpg)

The exported product version can be found in the "Products" tab in the Prism Project Browser.

## Creating Playblasts

To create and save a playblast you can open the State Manager from the Prism menu.

In the "Export" section click the "Playblast" button to create a "Playblast" state.

When the state is selected you can set the playblast settings on the right side in the State Manager.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and create a playblast of your scene.

![../../_images/houdini_playblast.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_playblast.jpg)

The playblast can be found in the "Media" tab in the Prism Project Browser.

## Rendering

To render your scene and save it to disk you can open the State Manager from the Prism menu.

In the "Export" section click the "Render" button to create a "Render" state.

When the state is selected you can set the render settings on the right side in the State Manager.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and create a render of your scene.

![../../_images/houdini_render.jpg](https://prism-pipeline.com/docs/latest/_images/houdini_render.jpg)

The render can be found in the "Media" tab in the Prism Project Browser.

If you have the Deadline plugin installed you will see an option to submit the render as a job to the Deadline render farm.

## Scene Building

Access

Result

An initial scenefile "v0001" with the comment "Scene Building" has been created. During the building process, all configured steps - such as "Set Framerange", "Set FPS", and "Import Products" - will be applied.

Scene Building Settings

Available steps can be configured in the Project Settings:

`Prism Settings > Project > Scene Building > Houdini`

![[Scene Building - Houdini Settings]](https://prism-pipeline.com/docs/latest/_static/plugins/houdini/Houdini_SceneBuilding_Settings.png)

Houdini Steps

The following Scene Building steps and their respective settings are available in Houdini:

| Set Shot Framerange: |  |
| --- | --- |
| Description: | In cases where the defined shot framerange does not align with that of the scene, the scene framerange will be updated. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |
| Framerange to apply: | The framerange can be set based on the `Shotrange` or on the `Shotrange + Handles`.  The default selection is `Shotrange`. |

| Set FPS: |  |
| --- | --- |
| Description: | If the defined shot FPS differs from FPS of the scene, the scene FPS will be updated. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |

| Set Resolution: |  |
| --- | --- |
| Description: | In case the defined shot resolution does not align with the resolution of the scene, the scene resolution will be synced. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |

| Import Products: |  |
| --- | --- |
| Description: | If products with tags are available, they will be imported automatically. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |
| Ignore Master Versions: | This can be enabled to import the latest product version instead of the master version.  It is disabled by default. |

| Import Shot Cameras: |  |
| --- | --- |
| Description: | If a shot camera product exists, it will be imported automatically. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |

| Run Code: |  |
| --- | --- |
| Description: | This step allows to run custom Python code. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |
| Code: | The code field accepts custom Python code for execution. |

| Apply Alembic Caches: |  |
| --- | --- |
| Description: | This step checks for available animation caches.  For each found cache the corresponding Surfacing product which is tagged with `static` will be imported.  Subsequently, the animation caches will be applied to each referenced Surfacing product. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |

Further Reading

*Alongside the Houdini specific information, additional details on Scene Building can be found on the [Scene Building](https://prism-pipeline.com/docs/latest/general/scene-building) page.*

## Solaris

Prism provides a deep Solaris integration with additional HDAs, new state types in the State Manager and nodegraph presets.

The Solaris integration is part of the [USD Prism plugin](https://prism-pipeline.com/docs/latest/plugins/USD/#plugin-usd).

## Adding Prism integration using environment variables

It is possible to use environment variables to add the Prism integration to Houdini instead of adding the Prism integration into the Houdini User Preferences.

The following environment variables need to be defined:

```
PRISM_ROOT = C:\Program Files\Prism2
HOUDINI_PATH = C:\ProgramData\Prism2\plugins\Houdini\Integration
```

These environment variables can be set in the system settings, a [package file](https://www.sidefx.com/docs/houdini/ref/plugins.html#using_packages) or in the [houdini.env](https://www.sidefx.com/docs/houdini/basics/config_env.html#setting-environment-variables) file.

To load the Prism Houdini plugin from a central location in your studio you can set the [HOUDINI\_PACKAGE\_DIR](https://www.sidefx.com/docs/houdini/ref/plugins.html#using_packages) environment variable and point it to a folder on your network storage. In that folder create a `Prism.json` file with the following content:

```
{
    "env": [
        {"PRISM_ROOT": "C:\\Program Files\\Prism2"
        }
    ],
    "path": "C:\\ProgramData\\Prism2\\plugins\\Houdini\\Integration"
}
```

## Troubleshooting

### When I open Houdini, the Prism Project Browser opens twice

This happens when specifics paths are added to the HOUDINI\_PATH environment variable twice. Usually this happens because of a misconfigured houdini.env file. A common mistake is to have a line like this in the houdini.env file: `HOUDINI_PATH = "...;$HOUDINI_PATH;&"`

To fix this problem you can change this line to: `HOUDINI_PATH = "...;$HOUDINI_PATH"`