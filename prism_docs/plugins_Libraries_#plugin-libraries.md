![[Logo: Libraries]](https://prism-pipeline.com/docs/latest/_static/banner_logos/libraries_logo.png)

## Libraries

The Libraries plugin adds access to multiple asset libraries to your projects.

## Overview

Libraries can contain textures, HDRIs, models, audio, scripts and any other kind of files.

It is possible to create project specific libraries, create libraries, which are available across multiple projects and add existing online libraries to download assets in different resolutions and formats.

![../../_images/libraries.jpg](https://prism-pipeline.com/docs/latest/_images/libraries.jpg)

## Setup

The plugin can be installed from the Prism Hub.

## Libraries

The Libraries are available in a tab named "Libraries" in the Project Browser.

Libraries can be enabled or disabled for each project.

The settings for this as well as other settings are available in the "Libraries" tab of the Prism Project Settings.

On the left side there are tabs for each active library.

Underneath there is a treeview to navigate the library.

On the right side you can see the available files at the selected location of the library.

You can double click folder to dive into them and double click in an empty area to move one level up.

To ingest files into the libraries you can simply drag&drop them from other applications (This is only available for some library types).

These types of libraries are available:

### Assets

This library lists all assets in your currently active project. You can import products from here and also access asset specific textures and files by double clicking an asset.

### Project Library

This library can contain project specific files, which are not specific to an individual asset.

The location of this library is defined by the "Textures" template in the folder structure settings of your project settings.

By default it will be here: `@project_path@/04_Resources/Textures`

### Poly Haven

This library integrates the free online library Poly Haven into Prism.

From here you can download HDRIs, textures and model for free and use them in your projects.

You can select different resolutions and fileformats before downloading assets.

The assets will be stored in the Prism project folder and are available to use by other team members as well.

![../../_images/libraries_polyhaven.jpg](https://prism-pipeline.com/docs/latest/_images/libraries_polyhaven.jpg)

You can view the library online [here](https://polyhaven.com/).

You can find details about the license of the Poly Haven assets [here](https://polyhaven.com/license).

In summary you can use and redistribute all assets for free without attribution even for commercial projects.

If you want to support Poly Haven you can do that [here](https://www.patreon.com/polyhaven/overview).

### GPU Open

This library integrates the free AMD GPU Open online MaterialX library into Prism.

You can download materials in the MaterialX standard with different texture resolutions.

These materials can be used for USD assets in different DCCs.

![../../_images/libraries_gpuopen.jpg](https://prism-pipeline.com/docs/latest/_images/libraries_gpuopen.jpg)

You can view the library online [here](https://matlib.gpuopen.com/).

### Custom Libraries

Custom libraries are similar to the Project Library, but can be stored outside of your project and can be shared across multiple projects.

You can add unlimited custom libraries in the "Libraries" tab in the Project Settings.

## Project Settings

The following settings are available in the Project Settings in the "Libraries" category:

### Use master texture versions

Enabled master versions for textures, which get exported from Substance Painter.

Master versions don't have a version number and are usually a copy of the latest numbered version.

They can be referenced in scenefiles and when the master version gets replaced with new textures, the filepaths in the scenefiles don't need to get relinked.

### Use library when importing assets

When enabled, the library window will open when the artists are about to import files in their scenefiles.

Usually this happens when clicking the "Import" button in the State Manager, but also in other cases like when clicking the "Import" tool in the Maya Prism shelf.

In the library window, artists can select their assets, products and versions to import.

It's also possible to open the Product Browser and select a product version to import there.

When disabled, the usual Prism Product Browser window will open.

### Generate thumbnails on disk

When enabled, Prism will save the generated thumbnail for files in the library to disk.

The next time the file is displayed, Prism will load the thumbnail from disk instead of generating a new one, which can improve performance significantly.

### Enable rstexbin conversion (Redshift)

When enabled, shows the option to convert image files to.rstexbin files when rightclicking files in the library.

The.rstexbin files are used by Redshift for optimized rendering speed.

### Use Asset Library

When enabled, shows a library of the assets in the current project.

### Use Shot Library

When enabled, shows a library of the shots in the current project.

### Use Project Library

When enabled, shows a project library, in which all project related files like HDRIs, textures, concepts, audio files, scripts and other files can be stored.

### Use Poly Haven Library

When enabled, shows the Poly Haven library, which provides free access to HDRIs, models and textures.

### Use GPU Open Library

When enabled, shows the GPU Open library, which provides free access to MaterialX materials.

### Custom Libraries

Custom libraries allow you to display the content of arbitrary locations in the libraries tab in the Prism Project Browser.

You can add as many custom libraries to your project as you like.

Libraries of type "Files" will display all files and folders of the selected location.

Libraries of type "Assets" can be used to display assets from other Prism projects. This makes it possible to create one Prism project, which acts as a studio asset library, which can then be added to other Prism projects and provide access to different products and versions of the studio assets.