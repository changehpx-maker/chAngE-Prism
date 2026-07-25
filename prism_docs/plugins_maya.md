![[Logo: Maya]](https://prism-pipeline.com/docs/latest/_static/banner_logos/maya_logo.png)

## Maya

This plugin integrates Prism into [Autodesk Maya](https://www.autodesk.com/products/maya).

Supported Maya versions: 2022+ (Python 3)

## Guides

This section provides an overview of the Prism-Maya integration, including the Basics, Extras and advanced USD workflows.

## Setup

The plugin can be installed from the Prism Hub. After the plugin is installed, the Prism integration needs to be added to the Maya preferences folder. This can be done in the Prism User Settings -> "DCCs apps".

This is the path, which should be selected for the integration (other Maya versions are possible): `%USERPROFILE%\Documents\maya\2026`

## Accessing Prism in Maya

Prism is available inside Maya from the "Prism" menu in the main menu bar or from the Prism shelf.

![../../_images/maya_menu.jpg](https://prism-pipeline.com/docs/latest/_images/maya_menu.jpg)
- save and version up your scene
- save, version up your scene and add a description/thumbnail
- open the Project Browser
- open the State Manager to import, export, playblast and render files
- open the Prism Settings

## Saving Scenefiles

You can save new scenefile versions using the options in the Prism menu or by opening the Project Browser and selecting "Create new version from current" in the context menu in the "Scenefiles" tab.

![../../_images/maya_saveVersions.jpg](https://prism-pipeline.com/docs/latest/_images/maya_saveVersions.jpg)

## Importing Objects

To import objects from your Prism project into Maya you can open the State Manager from the Prism menu, expand the "Import" section and click the "Import" button.

The Product Browser will open where you can select and import a product version by double clicking it.

Alternatively you can also rightclick a product version in the Project Browser and select "Import".

![../../_images/maya_import.jpg](https://prism-pipeline.com/docs/latest/_images/maya_import.jpg)

## Exporting Objects

To export objects from Maya into your Prism project you can open the State Manager from the Prism menu and click the "Export" button in the "Export" section.

This will create an export state where you can set your export settings and define which objects to export.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and export your objects.

![../../_images/maya_export.jpg](https://prism-pipeline.com/docs/latest/_images/maya_export.jpg)

The exported product version can be found in the "Products" tab in the Prism Project Browser.

## Creating Playblasts

To create and save a playblast you can open the State Manager from the Prism menu.

In the "Export" section click the "Playblast" button to create a "Playblast" state.

When the state is selected you can set the playblast settings on the right side in the State Manager.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and create a playblast of your scene.

![../../_images/maya_playblast.jpg](https://prism-pipeline.com/docs/latest/_images/maya_playblast.jpg)

The playblast can be found in the "Media" tab in the Prism Project Browser.

## Rendering

To render your scene and save it to disk you can open the State Manager from the Prism menu.

In the "Export" section click the "Render" button to create a "Render" state.

When the state is selected you can set the render settings on the right side in the State Manager.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and create a render of your scene.

![../../_images/maya_render.jpg](https://prism-pipeline.com/docs/latest/_images/maya_render.jpg)

The render can be found in the "Media" tab in the Prism Project Browser.

If you have the Deadline plugin installed you will see an option to submit the render as a job to the Deadline render farm.

## Scene Building

Access

![[Maya - Scene Building - Access Example]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya_SceneBuilding_AccessExample.png)

Result

An initial scenefile "v0001" with the comment "Scene Building" has been created. During the building process, all configured steps - such as "Set Framerange", "Set FPS", and "Import Products" - will be applied.

Scene Building Settings

Available steps can be configured in the Project Settings:

`Prism Settings > Project > Scene Building > Maya`

![[Scene Building - Maya Settings]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya_SceneBuilding_Settings.png)

Maya Steps

The following Scene Building steps and their respective settings are available in Maya:

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

| Create Model Hierarchy: |  |
| --- | --- |
| Description: | Creates a default "Model Hierarchy". |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |

| Import Products: |  |
| --- | --- |
| Description: | If products with tags are available, they will be imported automatically. |
| Apply to task: | Specifies the Entity, Department, or Task for which the step should be executed.  The default selection is `*-*-*`, meaning the step applies to all. |
| Mode: | Defines if products will be referenced (`Reference`) or imported (`Import`).  The default "Mode" is set to `Reference`. |
| Namespace: | Custom Maya namespaces can be defined which will be applied during import.  By default it will use the following "Namespace": `{entity}_{task}` |
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

*Alongside the Maya specific information, additional details on Scene Building can be found on the [Scene Building](https://prism-pipeline.com/docs/latest/general/scene-building) page.*

## Alembic Workflow

- [Alembic Workflow](https://prism-pipeline.com/docs/latest/plugins/maya/alembic-workflow/)

## Adding Prism integration using environment variables

It is possible to use environment variables to add the Prism integration to Maya instead of adding the Prism integration into the Maya User Preferences.

The following environment variables need to be defined:

```
PRISM_ROOT = C:\Program Files\Prism2
PYTHONPATH = C:\ProgramData\Prism2\plugins\Maya\Integration\scripts
MAYA_SHELF_PATH = C:\ProgramData\Prism2\plugins\Maya\Integration\shelves
XBMLANGPATH = C:\ProgramData\Prism2\plugins\Maya\Integration\icons
```

These environment variables can be set in the system settings or in the [Maya.env](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-8EFB1AC1-ED7D-4099-9EEE-624097872C04) file.

To load the Prism Maya plugin from a central location in your studio you can set the [MAYA\_ENV\_DIR](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-AE7BF762-0666-44D9-A275-75020684F838) environment variable and point it to a folder on your network storage. In that folder create a `Maya.env` file with the following content:

```
PRISM_ROOT = C:\Program Files\Prism2
PYTHONPATH = C:\ProgramData\Prism2\plugins\Maya\Integration\scripts
MAYA_SHELF_PATH = C:\ProgramData\Prism2\plugins\Maya\Integration\shelves
XBMLANGPATH = C:\ProgramData\Prism2\plugins\Maya\Integration\icons
```

## Troubleshooting

### I don't see the Prism shelf in Maya

This means that the Prism integration isn't added to Maya.

In Prism standalone go to the Prism User Settings -> DCC apps -> Maya and add the Prism integration to your Maya preferences folder.

If the preferences folder is already in the list, ignore that and add the Prism integration to the folder again.

### I see the Prism shelf, but get a warning when I try to open the Project Browser

This can happen when other Maya plugins are causing errors during the Maya startup.

Usually this is caused by errors in this file:

`%USERPROFILE%\Documents\maya\2024\scripts\userSetup.py`

You can see the error message by opening the Maya Output Window after Maya launched: Windows -> Output Window (usually at the top of the window when you scroll all the way up).

If you know Python you can try to fix that error.

Otherwise you can simply remove all the non-Prism related code in the userSetup.py file.

You can also remove the userSetup.py file completely and then add the Prism integration to the Maya preferences folder again from the Prism User Settings.