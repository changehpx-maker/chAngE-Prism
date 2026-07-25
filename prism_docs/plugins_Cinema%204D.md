![[Logo: Cinema 4D]](https://prism-pipeline.com/docs/latest/_static/banner_logos/cinema4d_logo.png)

## Cinema 4D

This plugin integrates Prism into [Maxon Cinema 4D](https://www.maxon.net/en/cinema-4d).

The plugin is now open source for all users.

This plugin has been tested with Cinema 4D 2024-2025. Other versions might work as well.

## Guides

The guides section covers the Prism-Cinema 4D integration.

![[Thumbnail: Cinema 4D - Basics]](https://prism-pipeline.com/docs/latest/_images/Cinema4D_Basics_thumbnail.jpg) [Cinema 4D](https://prism-pipeline.com/docs/latest/guides/cinema4d/#guides-cinema4d)

## Setup

The plugin can be installed from the Prism Hub.

After the plugin is installed, the Prism integration needs to be added to the Cinema 4D preferences folder.

This can be done in the popup after the plugin installation or in the Prism User Settings -> "DCCs apps".

This is the path, which should be selected for the integration (with different version numbers possible):

`%APPDATA%\Maxon\Maxon Cinema 4D 2025`

## Accessing Prism in Cinema 4D

Prism is available inside Cinema 4D from the "Prism" menu in the main menu bar.

![../../_images/c4d_menu.jpg](https://prism-pipeline.com/docs/latest/_images/c4d_menu.jpg)
- save and version up your scene
- save, version up your scene and add a description/thumbnail
- open the Project Browser
- open the State Manager to import/export files
- open the Prism Settings

## Saving Scenefiles

You can save new scenefile versions using the options in the Prism menu or by opening the Project Browser and selecting "Create new version from current" in the context menu in the "Scenefiles" tab.

![../../_images/c4d_saveVersions.jpg](https://prism-pipeline.com/docs/latest/_images/c4d_saveVersions.jpg)

## Importing Objects

To import objects from your Prism project into Cinema 4D you can open the State Manager from the Prism menu, expand the "Import" section and click the "Import" button.

The Product Browser will open where you can select and import a product version by double clicking it.

Alternatively you can also rightclick a product version in the Project Browser and select "Import".

![../../_images/c4d_import.jpg](https://prism-pipeline.com/docs/latest/_images/c4d_import.jpg)

## Exporting Objects

To export objects from Cinema 4D into your Prism project you can open the State Manager from the Prism menu and click the "Export" button in the "Export" section.

This will create an export state where you can set your export settings and define which objects to export.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and export your objects.

![../../_images/c4d_export.jpg](https://prism-pipeline.com/docs/latest/_images/c4d_export.jpg)

The exported product version can be found in the "Products" tab in the Prism Project Browser.

Supported formats are.abc,.obj,.fbx,.usda,.usdc,.rs,.ass and.c4d.

## Creating Playblasts

To create and save a playblast you can open the State Manager from the Prism menu.

In the "Export" section click the "Playblast" button to create a "Playblast" state.

When the state is selected you can set the playblast settings on the right side in the State Manager.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and create a playblast of your scene.

![../../_images/c4d_playblast.jpg](https://prism-pipeline.com/docs/latest/_images/c4d_playblast.jpg)

The playblast can be found in the "Media" tab in the Prism Project Browser.

## Rendering

To render your scene and save it to disk you can open the State Manager from the Prism menu.

In the "Export" section click the "Render" button to create a "Render" state.

When the state is selected you can set the render settings on the right side in the State Manager.

You can then use the "Publish" button at the bottom of the State Manager to execute the state and create a render of your scene.

![../../_images/c4d_render.jpg](https://prism-pipeline.com/docs/latest/_images/c4d_render.jpg)

The render can be found in the "Media" tab in the Prism Project Browser.

If you have the Deadline plugin installed you will see an option to submit the render as a job to the Deadline render farm.