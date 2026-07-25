## Project Browser

The Project Browser is the central tool in Prism for accessing files and data of your projects.

## Guides

This section explains how to work with the Prism Project Browser.

![[Thumbnail: Project Browser - Basics]](https://prism-pipeline.com/docs/latest/_images/ProjectBrowser_Basics_thumbnail.jpg) [Basics](https://prism-pipeline.com/docs/latest/guides/project-browser/basics/#project-browser-basics)

## Layout

The layout of the Project Browser is organized into different tabs, which are explained in more detail below.

In the main menu bar there are a couple of options and help information. On the right side of the menu bar you can edit your username (unless it's read-only because of your project or studio settings) and you can switch to a different active project.

## Scenefiles

The Scenefiles tab lets you access all the scenefile versions (sometimes called workfiles) of your project.

This is where your artists can save and load the files they are working on.

![../../_images/ProjectBrowser_Scenefiles.png](https://prism-pipeline.com/docs/latest/_images/ProjectBrowser_Scenefiles.png)

On the left side select an asset/shot, then a department and task and then you can view the existing scenefile versions for that task on the right side.

You can also create assets, shots, departments and tasks by double-clicking the lists or from the context menu. When a task is selected you can save a new scenefile version from the context menu or open an existing version by double clicking it.

External scenefiles can be ingested by drag&drop into the files table when a task is selected.

### Department Icons

Department icons are supported since v2.0.0.beta17.5 and default icons are included in Prism since v2.0.0.beta17.14.

Prism will look for icons in your project folder under `00_Pipeline\\Icons`. The filename of the icons should be the department name plus `.png`. For example `Animation.png`.

If you customized your department names or want to change the default icons, you can add/update the icons in the folder and restart Prism.

If your project was created with a Prism version before v2.0.0.beta17.14, you can find the default icons under:

`C:\\Program Files\\Prism2\\Presets\\Projects\\Default\\00_Pipeline\\Icons`.

From there you can copy them to the `00_Pipeline\\Icons` folder in your project.

## Products

The Products tab let's you view all the product versions of your assets and shots. Products are usually geometry caches like.fbx or.abc files, volume caches like.vdb files or other filetypes like.usd. Basically everything that gets exported from a scenefiles, which isn't considered a media file, is considered a product.

![../../_images/ProjectBrowser_Products.png](https://prism-pipeline.com/docs/latest/_images/ProjectBrowser_Products.png)

External files can be ingested as a product by drag&drop into the versions table when a product is selected.

Many file formats can be displayed in a 3d viewport when the [USD](https://prism-pipeline.com/docs/latest/plugins/USD/#plugin-usd) plugin is loaded.

## Media

The Media tab gives you access to all media versions of your assets and shots. Usually these files are renders or playblasts.

![../../_images/ProjectBrowser_Media.png](https://prism-pipeline.com/docs/latest/_images/ProjectBrowser_Media.png)

You can view a preview of your media files and open them in an external media player.

A wide range of fileformats are supported.

## Additional Tabs

The three tabs mentioned above are visible by default. Additional tabs might be visible depending on the plugins you have installed.

For example the [Libraries](https://prism-pipeline.com/docs/latest/plugins/Libraries/#plugin-libraries) plugin adds a "Libraries" tab for accessing textures, models, references and other files.

The [Project Management](https://prism-pipeline.com/docs/latest/plugins/Project%20Management/#plugin-projectmanagement) plugin adds a "Review" tab for media playlists and a "Tasks" tab for viewing assigned tasks.

See the documentation of these plugins for more information.

More tabs can be added by custom plugins.

## Creating Assets

Assets can be created in the Scenefiles, Products and Media tab by doubleclicking or using the context menu in the asset list.

Folders can be created to organize assets.

Besides the name, a description and thumbnail can be set for assets.

## Creating Shots

Shots can be created in the Scenefiles, Products and Media tab by doubleclicking or using the context menu in the shot list.

Every shot is part of a sequence.

Besides the name, a thumbnail and a framerange can be set for shots.

## Entity Meta Data

Assets and shots can have any number of meta data attached. The meta data can be added, edited and removed in the "Edit Asset" / "Edit Shot" window. This window can be opened by double clicking the entity thumbnail.

The meta data can be used to store custom information, but there are also some meta data settings, which Prism will understand:

| Name | Meaning |
| --- | --- |
| fps | This will override the fps value in the Project Settings. When opening a scenefile in this entity, Prism will warn the user if the fps in the scenefile doesn't match this value. (e.g. 25) |
| resolution\_x | This will override the x resolution in the Project Settings. When opening a scenefile in this entity, Prism will warn the user if the x resolution in the scenefile doesn't match this value. (e.g. 1920) |
| resolution\_y | This will override the y resolution in the Project Settings. When opening a scenefile in this entity, Prism will warn the user if the y resolution in the scenefile doesn't match this value. (e.g. 1080) |
| handles\_in | This will set the handles at the beginning of the shot. When opening a scenefile in this entity, Prism will warn the user if the startframe in the scenefile doesn't match the startframe of the shot - this value. (e.g. 6) |
| handles\_out | This will set the handles at the end of the shot. When opening a scenefile in this entity, Prism will warn the user if the endframe in the scenefile doesn't match the endframe of the shot + this value. (e.g. 6) |
| handles | This will set the handles at the beginning and at the end of the shot if handles\_in or handles\_out don't exist in the meta data of this entity. (e.g. 6) |