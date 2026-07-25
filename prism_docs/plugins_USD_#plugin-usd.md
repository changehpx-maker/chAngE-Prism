![[Logo: USD]](https://prism-pipeline.com/docs/latest/_static/banner_logos/usd_logo.png)

## USD

[Universal Scene Description](https://graphics.pixar.com/usd/docs/index.html) is a framework to manage data in CG productions.

## Overview

USD was originally developed by Pixar and is used in many big animation and visual effects studios. It allows to manage huge amount of data very efficiently. USD can store geometry, materials, cameras, lights and more in an universal format, which can be exchanged between many modern DCCs. This makes USD a great addition to Prism.

To use Universal Scene Description in Prism you need to install and load the Prism USD plugin. You can install the plugin during the Prism installation setup or at any point later on from the Prism Hub. You can open the Prism Hub from the first page in the Prism Settings dialog.

For a detailed explanation of the USD workflow have a look at this presentation:

<iframe src="https://player.vimeo.com/video/551545616?h=7f38c79137" width="640" height="360" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen=""></iframe>

## USD in the Project Browser

![../../_images/usd_project_browser.jpg](https://prism-pipeline.com/docs/latest/_images/usd_project_browser.jpg)

The USD plugin adds a 3D viewport to the Products tab in the Project Browser.

In this viewport USD files can be viewed in different shading modes and with different renderers.

## USD in DCCs

- [USD in Houdini](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_houdini/#usd-houdini)
- [USD in Maya](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_maya/#usd-maya)
- [USD in Blender](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_blender/#usd-blender)
- [USD in Substance Painter](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_substance_painter/#usd-substance-painter)
- [USD in Unreal Engine](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_unreal/#usd-unreal)
- [USD in ZBrush](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_zbrush/#usd-zbrush)

More and more DCCs are adding support for USD.

As this continues to evolve, Prism will add support for more DCCs and their USD integrations.

In the meantime it is possible to export alembic, fbx and obj files from DCCs, which don't support USD yet.

These alembic, fbx and obj files can then be referenced by USD files in Prism in order to take advantage of the USD workflow.

## Prism USD Editor

![../../_images/usd_editor.jpg](https://prism-pipeline.com/docs/latest/_images/usd_editor.jpg)

The Prism USD Editor provides options to view and edit the USD layer hierarchy and the Scenegraph USD Prim Hierarchy.

It can be opened from a button in the Products tab of the Project Browser or from the context menu when rightclicking USD files in various places in Prism.

**Layer Tree**

On the left side of the USD Editor a layer tree shows all the layers inside of the loaded USD file.

Layers can be added, removed or reordered.

It's also possible to switch the version of a layer.

The content of a layer can be shown and edited as raw text from the context menu.

**Scenegraph**

The center area of the USD Editor shows the USD scenegraph with the hierarchy of all USD prims of the composed USD stage.

It's possible create USD variants and references.

New prims can be added and existing prims can be deleted from the context menu.

**Viewport**

On the right side of the USD Editor a viewport shows the composed stage.

It's possible play back animations, view the stage from different cameras and switch between different available renderers.

A turntable can be rendered from here as well.

## User Settings

![../../_images/usd_user_settings.jpg](https://prism-pipeline.com/docs/latest/_images/usd_user_settings.jpg)

The following settings are available in the USD category in the Prism User Settings:

USD render executable (Husk) [#](#term-USD-render-executable-Husk "Link to this term")

This path specifies, which executable to use when rendering USD files.

It should point to the `bin/husk.exe` of an Houdini installation.

Prism will use this executable when rendering USD files from the Project Browser or when submitting USD render jobs from Houdini with specific submission settings.

See [here](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_houdini/#usd-lop-render) for more details.

Hython executable [#](#term-Hython-executable "Link to this term")

This path specifies, which hython executable to use the opening an USD viewport from Prism outside of Houdini, which runs in an Houdini environment.

This viewport can be opened using the "Open in Houdini viewport" option in the context menu of the USD viewport in Project Browser and the Prism USD Editor.

QuiltiX root [#](#term-QuiltiX-root "Link to this term")

This path specifies the root folder of.

If this is set, additional options to open MaterialX files in QuiltiX will become available in the Project Browser.

Loki root [#](#term-Loki-root "Link to this term")

This path specifies the root folder of [ShapeFX Loki](https://shapefx.app/).

If this is set, additional options to open USD files in Loki will become available in the Project Browser.

Show USD viewport in Products tab by default [#](#term-Show-USD-viewport-in-Products-tab-by-default "Link to this term")

This option controls if the USD viewport will be visible when the Project Browser opens.

Disabling this option can improve the startup time.

If disabled, the visibility of the viewport can still be toggled using the viewport button in the "Products" tab in the Project Browser.

Create Maya Usd Shelf Tools [#](#term-Create-Maya-Usd-Shelf-Tools "Link to this term")

When this option is enabled, Prism will add two additional shelf tools to the Prism shelf in Maya.

See [here](https://prism-pipeline.com/docs/latest/plugins/USD/usd_in_maya/#usd-maya-shelf) for more details.

Hydra Delegate: Arnold [#](#term-Hydra-Delegate-Arnold "Link to this term")

Enables the Arnold Hydra delegate in the USD viewports in Prism.

The path to the Arnold SDK must be specified.

See for more details.

## Project Settings

![../../_images/usd_project_settings.jpg](https://prism-pipeline.com/docs/latest/_images/usd_project_settings.jpg)

The following settings are available in the USD category in the Prism Project Settings:

Create USD container product on entity creation [#](#term-Create-USD-container-product-on-entity-creation "Link to this term")

If this option is enabled, a `USD` product will be created automatically when an asset or shot gets created.

> [!note] Note
> When the Prism project is connected to Shotgrid/ftrack/Kitsu, Prism doesn't get notified when new assets and shots get created and therefore the USD container won't get created automatically.
> 
> Use the `Create Asset-/Shot-Folders` button in the Project Management category of the Project Settings to trigger the USD container creation in these projects.

Create USD department layers automatically [#](#term-Create-USD-department-layers-automatically "Link to this term")

If this option is enabled, a USD department layer will be created when a department gets created for an asset or shot.

This department layer gets sublayered into the entity USD container automatically and can be viewed in the Products tab in the Product Browser.

Use relative paths [#](#term-Use-relative-paths "Link to this term")

This option enables relative paths instead of absolute paths, when layering or referencing USD files into other USD files.

Sublayer versions in USD master files [#](#term-Sublayer-versions-in-USD-master-files "Link to this term")

When product master versions are enabled in the Project Settings, each product can have a master version, which is usually a renamed copy of the latest numbered version.

If this option is enabled, Prism will not create a copy of the numbered version when updating a master version, instead a.usda file gets created as the master version, which sublayers the numbered version.

This has two advantages.

1\. The master file is very lightweight and therefore saves spaces and is fast to create.

2\. While.usdc files get locked, when accessed by other processes and can't get updated to newer versions while locked,.usda files don't have this problem. Updating.usda master files is always possible,

Therefore it's highly recommended to enable this option when using master versions.

Automatically update USD layer versions in entity/departmentlayer USD files [#](#term-Automatically-update-USD-layer-versions-in-entity-departmentlayer-USD-files "Link to this term")

When enabled, after publishing a new version of a department layer, Prism will automatically update the entity USD container and replace the old version of the department layer with the new version.

The same applies to updating department layers when a sublayer gets published.

If master product versions are enabled in the project settings, Prism will not create a new version of the entity USD container, because it expects that the master version of the departmentlayer is layered in the entity USD container and therefore no filepath needs to get updated in the entity USD container when a new departmentlayer version gets created.

Layer Order [#](#term-Layer-Order "Link to this term")

This list defines the order of layers, which Prism will use when layering usd files in other usd files.

This applies to departmentlayers as well as sublayers.

Layernames at the top of the list will be layered on top of layernames at the bottom of the list.

Similar to layers in Photoshop.

This means that downstream departments need to be ordered on top of the upstream departments.

Layernames can be rearranged using drag&drop.

In the context menu there are options available to add and remove layernames.

Available Renderer [#](#term-Available-Renderer "Link to this term")

This list defines, which renderers are available in the `Renderer` dropdown in the Prism Render Window, when rightclicking a USD file in Prism and selecting USD -> Render.

The rendering will be performed using the Houdini husk executable.

Therefore this list should contain the renderers, which are available in your Houdini environment.

Available Playblast Renderer [#](#term-Available-Playblast-Renderer "Link to this term")

This list defines, which renderers are available in the `Renderer` dropdown in the Prism Render Window, when rightclicking a USD file in Prism and selecting USD -> Playblast.

### Referencing external alembic files into USD files

USD supports referencing and layering alembic files, but this should be considered as a workaround and only be used if you need to deal with old assets in the alembic format.

It's recommended to convert alembic files to USD files to avoid problems and limitations further down the pipe.

Alembic support in USD is implemented as a plugin and might not be available in all DCCs.

To use any alembic or obj file in a USD container of an asset or a shot you have to create a department layer first.

Go to the "Products" tab in the Prism Project Browser and select and asset or a shot.

Rightclick the "Products" list and select "USD" -> "Create department layer".

You can create a layer for any existing departments in your project or choose "Custom..." to create a new department.

When the department layer is created you can drag & drop an alembic file into the "Versions" list to copy it into the Prism folder structure.

When the version has been created you can rightclick the version an choose "USD" -> "Set as department layer in USD container".

This will create a new version of the USD container, which references in the select alembic file.

The USD container can now be imported into any DCC, which supports USD imports.

It is also possible to create sublayers for department layers from the context menu of the "Products" list to have more control over the composition of the USD container.

## Hydra Delegates

A Hydra delegate is a type of renderer, which can render USD scenes natively and which can be integrated tightly in almost any tool, which supports USD.

In Prism Hydra delegates can be used to playblast and render USD scenes and also to view USD files in the USD viewport in the standalone Project Browser.

In the "USD" tab of the Prism User Settings the different available Hydra delegates can be enabled/disabled.

After the settings for the render delegates are changed a Prism restart is usually required.

The following is a list of available Hydra delegates in Prism and how to set them up.

### GL (Storm)

The GL renderer is the default Hydra delegate in the Prism USD viewport.

It is available out of the box after installing the Prism USD plugin.

It supports geometry, basic light and materials and has the fastest refresh times.

This renderer looks similar to other viewport renderers in commonly used DCCs.

### Arnold

To use the Autodesk Arnold Hydra delegate in Prism you need to download the "Arnold SDK", which you can download for free in your Autodesk account [here](https://manage.autodesk.com/products/arnol?platform=WIN64).

> [!note] Note
> Prism 2.0.15 and later requires "Arnold SDK 7.3.6.1 for Windows". Earlier versions of Prism require "Arnold SDK 7.2.5.2 for Windows".

In the "USD" category of the Prism User Settings the path to the Arnold SDK must be specified.

You can use Arnold and it's Hydra delegate for free, but if no Arnold license was found a watermark will be rendered into your images.

Once Arnold is enabled, restart Prism and then Arnold becomes available in the "Renderer" menu at the top of the USD viewports in Prism.

## QuiltiX

QuiltiX is an open source MaterialX editor, which can be used to create and edit materials for USD assets.

A free download is available [here](https://prism-pipeline.com/quiltix).

![../../_images/quiltix.jpg](https://prism-pipeline.com/docs/latest/_images/quiltix.jpg)

Prism and QuiltiX can be used together for powerful material authoring workflows.

To integrate Prism and QuiltiX the QuiltiX root folder must be set in the Prism User Settings -> USD tab.

The Prism-QuiltiX integration can be found in a few places:

**In Prism:**

- If you have the "Texture Library" plugin installed you can rightclick any.mtlx files in the libraries and select "Open in QuiltiX..." from the context menu. This is especially useful when you have the "GPU Open" material library enabled in your project settings, which allows you to download free MaterialX files.
- In the Prism Usd Editor you can rightclick any MaterialX layers in your Usd layerstack and select "Edit in QuiltiX..." to open the MaterialX file in QuiltiX and also load the Usd stage including geometry into the QuiltiX viewport.

**In QuiltiX:**

If you opened QuiltiX from within Prism using the options mentioned above, there are a few additional features available in QuiltiX:

- The scenegraph and the viewport widget are replaced with the Prism scenegraph/viewport widgets. This allows you to modify the scenegraph hirarchy and use additional controls in the viewport. The viewport toolbar can be opened using the shortcut "x".
- A new Prism menu in the QuiltiX menu bar allows you to save you material as a new version. This requires that the.mtlx file is saved as a product in your Prism project. You can rightclick a.mtlx file layer in the Prism Usd Editor and select "Copy material to entity context" to save a material from a custom location as a product in Prism.
- In the "View" menu you can find a new "Libraries" option, which integrates the Prism libraries into QuiltiX. From here you can drag&drop HDRIs, textures and materials from your library into QuiltiX. You can also save your material into a library by rightclicking in an empty area of any of your libraries and select "Save current nodegraph...".

## ShapeFX Loki

[ShapeFX Loki](https://shapefx.app/) is a powerful USD editor, which can be used to author and analyse the content of a USD stage.

From the Prism Project Browser you can open USD files in Loki.

![../../_images/loki_menu.jpg](https://prism-pipeline.com/docs/latest/_images/loki_menu.jpg)

For that you need to download and install Loki first and then add the path to the Loki installation in the Prism User Settings -> USD -> Loki root.

A full Prism integration for Loki is planned for the future.

## USD workflow examples

### Example Projects

**Houdini USD example project**

This example shows a basic setup of a USD asset with materials and a simple animation and lighting in a shot. [Download](https://service.prism-pipeline.com/api/service/links/projects/usd_demo1)