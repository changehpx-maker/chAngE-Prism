![[Logo: Open RV]](https://prism-pipeline.com/docs/latest/_static/banner_logos/openrv_logo.png)

## Open RV

This plugin integrates Prism into the open source media player Open RV. It also support the commercial version of Autodesk RV.

## Overview

The purpose of this plugin is to create a seamless review workflow, by having access to the media of a Prism project within RV and exporting notes and annotations back to the Prism project.

Renders, playblasts and other media files in a Prism project can be easily accessed from inside RV with this plugin. Either by browsing asset and shot media versions or by accessing playlists. The RV annotation tools can be used to mark specific frames and then attach these annotations to notes of a Prism version. These annotations are then accessible in Prism within any DCC.

![../../_images/rv_overview.jpg](https://prism-pipeline.com/docs/latest/_images/rv_overview.jpg)

The source code of Open RV can be found [here](https://github.com/AcademySoftwareFoundation/OpenRV). At the time of writing there is no official executable available. Because of legal concerns we cannot make an Open RV executable publicly available. For help with building Open RV or any related questions please contact the Prism support.

## Setup

This plugin can be installed using the Prism Hub like any other plugin.

When the plugin is loaded, the Prism integration needs to be added to the RV user settings folder.

In the Prism User Settings in the "DCC apps" -> "Open RV", the integration can be added. Alternatively it can also be added in the Prism installer or by using the setup.bat in the Prism install directory.

The integration should be added to the RV user preferences, which is here by default: %APPDATA%/RV. This folder gets created when you launch RV for the first time. You can also create this folder manually to add the Prism integration if you haven't launched RV yet.

Once this is done you can launch RV and you will see a "Prism" menu in the main menu bar.

![../../_images/rv_menu.jpg](https://prism-pipeline.com/docs/latest/_images/rv_menu.jpg)

You can view the plugin details in the "Packages" tab of the RV Preferences window.

![../../_images/rv_plugin_details.jpg](https://prism-pipeline.com/docs/latest/_images/rv_plugin_details.jpg)

## Media Browser

The Media Browser let's you browse the assets and shots of a Prism project. This is basically the same as the "Media" tab in the Prism Project Browser. You can doubleclick a version or drag it into the RV viewer to view the media.

![../../_images/rv_media_browser.jpg](https://prism-pipeline.com/docs/latest/_images/rv_media_browser.jpg)

## Playlists

The playlists panel gives access to media playlists of a Prism project. This can be dailies playlists for example. This panel is similar to the "Review" tab of the Prism Project Browser. Doubleclicking a media item or the preview will open the media in the RV viewer. It is also possible to select multiple media items and use the "Play" option of the rightclick menu to create a new sequence view in RV and play all selected media in sequence. The Project Management Prism plugin needs to be enabled to open this panel.

![../../_images/rv_playlists.jpg](https://prism-pipeline.com/docs/latest/_images/rv_playlists.jpg)

## Notes and annotations

The notes panel will display some information, notes and replies of the currently viewed media version. It is possible to change the status of the media version using the rightclick menu of the info are at the top of the panel. When creating new notes and replies, there is an option to attach the currently active frame of the RV viewer. This frame can have annotations created using the RV annotations tool (F10). The Project Management Prism plugin needs to be enabled to open this panel.

![../../_images/rv_notes.jpg](https://prism-pipeline.com/docs/latest/_images/rv_notes.jpg)

## Adding Prism integration using environment variables

To load the Prism OpenRV plugin from a central location in your studio you can set the [RV\_SUPPORT\_PATH](https://aswf-openrv.readthedocs.io/en/latest/rv-manuals/rv-user-manual/rv-user-manual-chapter-ten.html#package-support-path) environment variable and point it to a folder on your network storage.

In that folder create a `Python/prism.py` file with the following content:

```
import os
import sys

def createMode():
    os.environ["PRISM_ROOT"] = "C:\\Program Files\\Prism2"
    rvPlugin = "C:\\ProgramData\\Prism2\\plugins\\OpenRV"
    sys.path.append(rvPlugin + "/Scripts")
    from Prism_OpenRV_Mode import PrismMode
    return PrismMode()
```

Copyright of project images shown in screenshots belongs to Fleng Entertainment & Tumblehead