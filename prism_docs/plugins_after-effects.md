![[Logo: After Effects]](https://prism-pipeline.com/docs/latest/_static/banner_logos/aftereffects_logo.png)

## After Effects

This plugin integrates Prism into [Adobe After Effects](https://www.adobe.com/products/aftereffects.html).

This plugin has been tested with After Effects 2024-2026. Previous versions might work as well.

## Guides

The guides section covers the Prism-After Effects integration.

![[Thumbnail: After Effects - Basics]](https://prism-pipeline.com/docs/latest/_images/AfterEffects_Basics_thumbnail.jpg) [Basics](https://prism-pipeline.com/docs/latest/guides/after-effects/basics/)

## Setup

The After Effects plugin can be installed from the Prism Hub.

Once the plugin has been installed, the Prism integration needs to be added to the After Effects preferences folder. This can be done in the popup after the plugin installation.

Alternatively, the Prism integration can be added to After Effects in the Prism Settings:

`Prism User Settings > DCCs apps > After Effects > Add.`

The following path should be selected for the integration:

`%APPDATA%\Adobe\CEP\extensions`

For Mac OS, please refer to the documented extension folders [here](https://github.com/Adobe-CEP/CEP-Resources/blob/master/CEP_12.x/Documentation/Debugging%20Handbook.md#12-extension-folders).

## Accessing Prism in After Effects

`Window > Extensions > Prism.`

The appearing "Prism Menu" window is dockable (2) anywhere in After Effects.

![[After Effects - Access]](https://prism-pipeline.com/docs/latest/_static/plugins/after-effects/AfterEffects_Access.png)
- save and version up your scene
- save, version up your scene and add a description/thumbnail
- open the Project Browser
- import media from your Prism project
- check if updated media versions are available
- open the Prism Settings
- open the Render Setup

## Saving Scenefiles

New scenefile versions can be saved via the Prism Menu or by opening the Project Browser and selecting "Create new version from current" from the context menu in the "Scenefiles" tab.

![[After Effects - Scenefiles]](https://prism-pipeline.com/docs/latest/_static/plugins/after-effects/AfterEffects_Scenefiles.png)

## Importing Media

To import media files from the Prism project into After Effects, select "Import Media..." to open the import dialog. Choose one or more Shots and select one of the available media Identifier:

![[After Effects - Import]](https://prism-pipeline.com/docs/latest/_static/plugins/after-effects/AfterEffects_Import.png)

Alternatively, media files can be added via the Project Browser. Right-click on any of the media files in the "Media" tab and select "Import images..." from the context menu or simply drag and drop the media files into After Effects.

## Check for New Versions

To see if new media versions are available select "Check for New Versions..." from the Prism Menu. Prism will show a notification pop-up for all outdated media versions.

## Rendering Media

To render an After Effects composition and save it to disk the "Render Setup" can be opened from the Prism menu.

The following settings can be configured:

- Entity: Defines the output location, usually preselected based on the scenefile.
- Identifier: Name under which the render output is located.
- Comment: Option to add a comment to the render output.
- Composition: Choose which After Effects "Composition" should be used.
- Template: A render settings template can be selected from the dropdown. Templates can be modified or added in the After Effects Render Queue panel.

To render the composition, click the "Render" button:

![[After Effects - Render]](https://prism-pipeline.com/docs/latest/_static/plugins/after-effects/AfterEffects_Render.png)

Alternatively, compositions can be added to the queue by clicking the "Add to Render Queue" button.

In order to add the composition to the Adobe Media Encoder (AME) right-click on the "Add to Render Queue" button and select "Add to Media Encoder Render Queue".

The render output can be found in the "Media" tab of the Prism Project Browser:

![[After Effects - Render Output]](https://prism-pipeline.com/docs/latest/_static/plugins/after-effects/AfterEffects_RenderOutput.png)