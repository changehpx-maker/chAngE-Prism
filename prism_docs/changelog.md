## Changelog

## Prism 2.1.2

- redesigned Scene Building Options in the Project Settings
- the IO Tools are now a separate plugin (Pro)
- added numerous export settings for USD exports in Maya
- added support for viewing.pdf files in the Media tab
- added options to toggle visibility of omitted assets and shots in the Project Browser
- added option to un-omit assets and shots
- added support for importing and exporting Houdini tool recipes
- added support for saving selected Houdini nodes as tool recipe in the Libraries
- added support for slapcomps on the Prism Render LOP in Houdini
- added support for importing HDAs in Houdini directly from Library tab in the Project Browser
- added support for rendering USD files using the Redshift commandline executable
- added support for rendering USD files using the Arnold commandline executable (kick) on Deadline
- added support for importing fbx files with existing Interchange templates
- added new GUI for creating new node types in the Execution Graph
- added option to change the nodetype when exporting nodes in the Execution Graph
- added option to zoom using alt + RMB in the Execution Graph
- added option to define disabled plugins in the project settings
- converting media in the Project Browser places the new file now in the same folder as the source files (can be changed using env vars)
- Houdini playblasts will not use a new viewport now to avoid display differences (can be changed using PRISM\_HOUDINI\_PLAYBLAST\_USE\_NEW\_VIEWPORT env var)
- fixed a limitation that odd media couldn't be converted to mp4 files in some cases
- fixed a color shift in mov conversions in some cases
- fixed an error when loading state presets in the State Manager
- fixed a bug that the list of objects to export in Maya was changed in some cases
- fixed an error when using the "Send to..." feature in some cases
- fixed dozens of additional bugs and small issues

## Prism 2.1.1

- added the Prism Execution Graph to the Prism Plus plan (previously in Early Access)
- added numerous new nodes and improvements to the Execution Graph
- added a new scene building feature, which sets up scenes with one click
- added options to assign tags to products in the State Manager
- added option to select from available assets to export in Maya (instead of selecting objects in the Outliner)
- added new tool to export multiple assets from a Maya scene at once
- added new tool to manage renders for multiple shots and renderpasses on the Prism Render LOP in Solaris
- added option to display items in the library as a list
- added search for all library types
- added a redesigned Photoshop plugin for 2026+ (UXP)
- added support for ZBrush 2026.1
- added episode support in Unreal Engine
- added support for substep caching in Houdini
- added options to reorder modifiers in the Media Converter
- added Default Preset Scenes to the Free plan (previously in the Plus plan)
- added State Defaults and State Presets to the Free plan (previously in the Plus plan)
- added support for referencing Maya files with relative paths
- added option to add media version to playlist after publishing to Kitsu/Shotgrid/ftrack
- added option to publish media manually after rendering from the WritePrism and Write node in Nuke
- added support for checking DeepRead nodes in Nuke for updated media versions
- added new USD sanity check to find undefined prims with only an "over" specifier
- redesigned the ingest tool
- several improvements for the delivery and version zero tools
- improved grouping and selection option in the map list in the Substance Painter Export window
- significant speed improvements when copying files and folders in Prism
- fixed some errors with multi layer exr rendering in Blender 5
- fixed an error when exporting USD layers with the Prism Filecache LOP in Houdini in some cases
- fixed a bug that the disabled camera override in Solaris Render LOP was still applied in some cases
- fixed a bug that prevented changing blender library links when library overrides were applied to an object
- fixed an error when loading Prism in hython on Linux

## Prism 2.1.0

- added new plugin Execution Graph, a node based automation tool, as Early Access
- the After Effects plugin is now open source and part of Prism Free
- updated to Python v3.13
- updated USD to v25.11
- added initial support for Linux and MacOS (only some plugin are supported currently)
- added IO tools for ingesting, version zeros and delivery workflows (beta, Pro)
- added option to add previews to products
- added option to import all connected assets of a shot in the shot context menu of the Project Browser and the State Manager
- added option to connect the same asset multiple times to a shot
- added option to write out USD file sequences from SOPs in Houdini
- added option to the Prism Import LOP in Solaris to load filesequences using the Geometry Clip Sequence LOP
- added option to execute Prism Filecache LOPs in Houdini multiple times with different context options and setting overrides
- added support for overriding node parameters per execution on Prism Render LOP and Prism Filecache LOP in Houdini
- added option to set USD renderpass on Prism Render LOP in Houdini
- added support for specifying USD Render Passes in the Prism Standalone USD Render submission settings
- added options to create USD variants in Maya
- added option to export USD animation curves from Maya
- added option to export Maya USD caches as file per frame (Value Clips)
- added option to import rigs from USD assets in Maya
- added multiple layout tools for the Maya Sequencer
- added options to change the Alembic export settings in Maya
- added option to set default USD Up Axis in the Project Settings
- added option to set default USD Meters per Unit in the Project Settings
- added sanity checks for USD files
- added support for audio in the Media Converter
- added support for converting media with odd resolution to mp4 files using the Media Converter
- added env var PRISM\_MEDIA\_CONVERSION\_OUTPUT\_MODE to define where to save converted media (version\_suffix, same\_folder, next\_version)
- added env var "PRISM\_RENDER\_LAYERS\_ALIGN\_VERSIONS" to disable the version alignment for Maya renderlayers
- added option to update the path from Arnold standins in Maya instead of replacing the standin
- added option to set the version explicitly on Nuke Write nodes
- added option to load.nk files in Nuke as LiveGroups and Precomps
- added new tool to view and update all media versions in a nuke script
- added support for tracking external dependencies in Nuke
- added support for Blender 5.0
- added option to export and import.glb files in Blender
- added support for Unreal Engine 5.7
- added option to import.glb files in Unreal Engine
- added option to render multiple takes in C4D
- added option to import multiple media identifiers at once into After Effects
- added support for exporting.psd files from Photoshop
- added support for previewing.psd files in the Media Browser
- added option to create assets from a timeline in Resolve
- added a search bar and favorites to the recent project list
- added option to activate the Prism Plus trial from the Prism Hub
- added env var PRISM\_ACCESS\_TOKEN to set the access token used for acquiring licenses
- added option to show only tasks, which are assigned in Shotgrid, ftrack, Kitsu in the Project Browser
- added support for sync asset-shot links from FTrack
- publishing to Shotgrid/ftrack/Kitsu from the State Manager uses now the taskname of the current scenefile instead of asking every time to which task the published version should be linked to
- fixed a bug that scenefile versioning didn't work correctly when episodes and local project folders were used
- fixed an error when creating a renderstate in Maya when Redshift is set as the active renderer and AOVs are used
- fixed a bug that the USD layer muting didn't work in Houdini if the asset name contained a space
- fixed an error when creating an USD Export state in Blender in some cases
- fixed a bug that the shot USD container wasn't updated correctly in some cases when not using master versions
- fixed a bug that absolute paths of referenced USD files were converted to relative paths during the USD export in Maya in some cases
- fixed a bug that USD renderjobs submitted from Prism standalone failed when multiple frames were rendered
- fixed a bug that the camera override for playblasts didn't work in C4D
- fixed a bug that in some cases only Windows admins had permissions to install and uninstall plugins
- removed support for Python 3.7

## Prism 2.0.18

- added new Solaris templates and simplified the USD workflows for all departments in Houdini (see Prism Guides for details)
- added support for Unreal Engine 5.6
- added support for exporting and importing Maya animation curves (.atom)
- added option to configure multiple external Media Players
- added option to render USD jobs using the Deadline Karma plugin
- added support for reparenting USD prims in the USD editor using drag&drop
- added support for rendering USD files using Arnold kick
- added new simplified USD layer publish windows in Maya
- added syntax highlighting when viewing USD files as text
- added option to save legacy exrs using the Prism Render LOP
- added options to set up variants, LODs, sublayers and loading product sequences using Prism Actions from the context menu in Solaris
- added options to set comments on the Prism Filecache/Render nodes in Houdini
- added option to write the USD sample frame to the Houdin Prism Filecache SOP
- added support for assigning materials when drag&drop.mltx files into Solaris
- added options for orientation and unit conversion to Blender USD exports
- added options for Frame Step and Frame Sample to Maya USD exports
- added a work layer for USD stages in Unreal
- added multiple new options to the export window in Unreal when exporting USD layers
- added option to convert units when importing products into Unreal
- added support for downloading PolyHaven textures as MaterialX
- added support for float FPS values in the Media Converter
- added option to combine media files in the Media Converter
- added support for resolution independent burn-ins and cropping in the Media Converter
- added support for viewing alpha and other mono channels of exr files in the Media tab
- added support for reading and writing mxf media files
- added several improvements to the Blender AOV workflow
- added option to load shots in context in OpenRV
- added "Import Media" option to After Effects to import media from multiple shots at once
- added option to add renderjobs in After Effects to the Media Encoder Queue
- added option to replace specific footage items in After Effects with a different media version
- added option to update outdated footage items in After Effects
- added support for rendering multiple Maya renderlayers into the same version of the same identifier
- added support for mp4 with audio playblasts in Maya without having quicktime installed
- added support for opening USD files in the Prism USD Editor by doubleclicking them in the Product Browser
- added artist username to Shotgrid publishes from Deadline jobs
- added option to define environment variables for Deadline job in the Project Settings
- added option to submit custom Python script jobs to Deadline
- added option to create tasks in Shotgrid/ftrack/Kitsu
- added option to Write node in Nuke to publish media to Shotgrid/ftrack/Kitsu after rendering
- added option to submit Shotgrid/ftrack/Kitsu publishes to the farm from the Project Browser
- added the option to open a Python Console in the current process (press CTRL to open it instead in a new process)
- added "PRISM\_USE\_STATE\_COMMENTS" env var to enable a comment field per state, which takes precedence over the State Manager comment during publish
- added "PRISM\_SHOW\_DEFAULT\_SCENEFILE\_PRESETS" env var to hide the default scenefile presets
- changed the "Copy" option (which copies the file) in context menus to "Copy Path". The old behavior can be activated using the "PRISM\_COPY\_FILE\_CONTENT" env var
- doubleclicking a layer in the USD editor opens the layer text window now
- master versions are now hidden by default in the USD Editor
- fixed a bug that setting frameranges in Houdini could have rounding errors in some cases
- fixed a bug that the dependency state in Houdini didn't work
- fixed a bug that rendering as previous version in Nuke didn't work correctly in some cases when submitting the render to Deadline
- fixed a bug that env vars were not evaluated correctly in filepaths in Nuke 15.2
- fixed a bug that filesequences were not detected when dropping or importing media into Nuke in some cases
- fixed a crash when opening the Media Converter in some cases
- fixed an error when submitting a scenedescription render to Deadline with the "Export scene description locally" option enabled
- fixed an error when exporting the whole scene in 3ds Max in some cases
- fixed an error when importing USD files in Substance Painter
- fixed an error when creating USD department layers for assets with invalid characters in their name
- fixed a bug that a wrong USD timecode could be set in entity USD containers when updating departmentlayers in some cases
- fixed a bug that Maya export jobs couldn't get submitted to Deadline
- fixed a bug that the "Parent USD Prim" setting in the Maya USD Export didn't work for material prims
- fixed a bug that the USD render jobs could fail in some cases when there were spaces in the jobname
- fixed a bug that updated shot products in Unreal where not detected
- fixed a bug that Kitsu asset playlists didn't sync correctly to Prism in recent Kitsu versions
- fixed a bug that publishes to Kitsu from identifier with underscores where not linked correctly to the media version in Prism

## Prism 2.0.17

- added a 6 hour licensing grace period when the internet connection is temporarily not available or the license server is not responding
- added support for syncing fps and resolution from Kitsu to Prism
- added support for importing and exporting USD files in 3dsMax
- added option to convert paths in USD files from absolute to relative in the Project Browser
- added support for converting absolute paths to relative paths when exporting USD files in Maya when relative paths are enabled in the Project Settings
- added PRISM\_USD\_DFT\_PAYLOAD\_PARENT env var to specify the parent prim when generating Layout USD stages or loading assets using the Prism Import LOP
- added support for new variables in the burnin in the Media Converter: sourcepath, sourcefilename, targetpath, targetfilename
- added option to view available variables for the overlay of the current media in the Media Converter
- submitting a renderjob in Nuke to Deadline increments the Nukescript version now
- fixed a bug that Karma deep renders couldn't be written out as a sequence
- fixed an error when toggling the active state of a Studio in the studio settings
- fixed an error when editing the raw text of.usdc files in the USD Editor
- fixed a bug that an incorrect path was added to the Houdini Layout LOP in some cases
- fixed a bug that the identifier on Nuke Write nodes wasn't used when submitting jobs to Deadline

## Prism 2.0.16

- added support for Nuke 16
- added support for saving job submission settings between Nuke sessions
- added option to group identifiers in the media tab
- added option to ungroup product groups
- added support for Solaris tile rendering and assembly for single frame Deadline jobs
- added option to use a more complex USD asset structure with payload and class primitives
- added option to insert shots between existing shots in Solaris multi-shot setups
- added support for Takes on the Prism Filecache SOP
- added support for selecting and rendering through USD cameras in Maya
- added a "shot + 1" option for frameranges to account for motion blur
- added the PRISM\_JOB env var to the Houdini File Browser
- added option to set environment variables for different Prism Versions in the Launcher
- added support for adding the Blender Prism integration in the Blender user preferences instead of the Blender installation folder
- added a retry option if Houdini failed to save the scenefile
- added a new "Default" task preset for shots
- added env var PRISM\_MAYA\_RES\_GATE to set the preferred resolution gate for playblasts
- added experimental option to use env var PRISM\_VERSION\_UP\_AFTER\_PUBLISH to increment the scenefile version after publishing instead of before publishing
- fixed a bug that muted layerpaths in the Mute Departments LOP could have backslashes, which isn't supported in Houdini
- fixed a bug that the LOP Render node wasn't executed when settings overrides were applied
- fixed an error when enabling the USD layer settings on the Prism Filecache SOP in Houdini
- fixed a bug that USD render products could be saved in a wrong folder when the outputfolderpath contained a dot
- fixed an error when exporting alembic files using the USD Export state in Blender
- fixed a bug that the camera of a USD stage wasn't set active when opening the viewport in the USD Editor
- fixed a bug that only one asset was imported when selecting multiple assets to import in the Library window
- fixed some problems with the SHOT context option on Deadline
- fixed a bug that the Arnold Hydra delegate wasn't working in Prism standalone in some cases
- fixed a bug that Maya Deadline renders with renderlayers could have a wrong outputpath
- fixed an error when using the Deadline submission for Maya playblasts
- fixed a bug that the "Frames per task" in the Deadline submission settings could be set to 0, which is invalid
- fixed a bug that the file knob's value in old Nuke scripts could get replaced with an expression in some cases
- fixed an error when creating a read node from a write node in Nuke
- fixed a bug that launching DCCs from the Project Browser in a Launcher environment didn't work in some cases
- fixed a bug that identifier in the media tab could get displayed twice in some cases
- fixed a bug that Deadline pools and groups could appear twice in the job submission settings dropdowns
- fixed a bug that some Deadline submission settings were not saved between sessions
- fixed a bug that RV annotations couldn't get uploaded to ftrack and Kitsu in some cases
- fixed an error when creating USD departmentlayers for ftrack entities
- fixed an error when creating an asset while connected to Kitsu
- fixed an error when creating shots in Kitsu in some cases
- fixed a bug that the Shotgrid/ftrack/Kitsu publish didn't work when submitted as Deadline job
- fixed a bug that no notes could be added to external media in OpenRV
- fixed an error when creating new external media versions in some cases
- fixed a bug that the list of users in the tasks tab was not refreshed correctly when connected to Shotgrid in some cases
- fixed a bug that media versions v0000 couldn't get published to ftrack
- fixed a bug when adding Prism integrations from network drives to DCCs

## Prism 2.0.15

- added options to set OCIO working color space, display and view transforms in the project settings, which will be used when viewing media in Prism and when publishing media to Shotgrid/ftrack/Kitsu
- added option to add attachments to notes and replies when using the Prism Project Manager
- added support for alpha channels in Prores 4444 conversions
- added option to specify which existing render job settings to use for Unreal Engine renders
- added option to create cameras automatically for imported shots in Unreal Engine
- added option to not override the output format of renderjobs in Unreal Engine
- added option to add jobs for shots to Unreal Movie Render Queue without starting the render
- added support for rendering multiple USD render products with one Prism LOP Render node
- added option to disable executions on the Prism LOP render node in Solaris
- added default USD prim hierarchy for shot department layers
- added button to select valid UFE path for the "Parent USD Prim" in the USD Export state in Maya
- added option to reload the Project Browser, State Manager and Prism Settings by pressing the CTRL key when opening the tools
- added support for using ffmpeg to generate preview images if OIIO is not available
- added "PRISM\_NUKE\_EXE" env var to generate thumbnails with Nuke when OIIO can't be loaded
- added env var PRISM\_SOLARIS\_DFT\_PAYLOAD\_PARENT to change the default parent on an Import LOP
- added env var PRISM\_SOLARIS\_SHOW\_ONLY\_SHOTS\_IN\_SCENE to set if the shotmenu in Houdini shows all shots or only existing shots in the scene
- updated the USD libraries to v25.02, MaterialX to v1.39.2 and PySide6 to v6.8
- the camera mask is now enabled by default in the USD viewport
- when publishing files with the Maya shelf tools, the scenefile will now be saved and versioned up based on the settings in the State Manager
- updated doubleclick and rightclick options of some Maya shelf tools
- the shot menu in Houdini is now added automatically when the Prism integration is added to Houdini
- the WritePrism node in Nuke is now disabled by default. The Prism menu on the default Write node should be used instead
- fixed a bug that some products were not displayed in the Product Browser when using the "Link products and media to tasks" option
- fixed a bug when opening apps with the Launcher environment from the Project Browser in some cases
- fixed a bug that the PRISM\_ROOT env var wasn't set when opening a DCC from the Project Browser with a Launcher executable override
- fixed an error when viewing Kitsu notes in Prism with attachments other than image files
- fixed a bug that double backslashes in env vars were converted to single backslashes in Houdini in some cases
- fixed an error when loading a HDA in Houdini in the State Manager in some cases
- fixed an error when drag&drop files into some Houdini pane tb types
- fixed a bug that the imported nodes in Houdini had a different name when relative paths are enabled in the project settings
- fixed a bug that the Houdini shot context got changed during the publish in some cases
- fixed an error when using the "Asset Department" preset in the Solaris
- fixed a bug that the LOP render node didn't render the nodeinput in some cases
- fixed a bug that the Prism Filecache LOP didn't write USD files with relative paths even if relative paths were enabled in the Project Settings in some cases
- fixed a bug that the LOP Import node could switch to Payload after duplicating it in some cases
- fixed a bug that the scaling in the Import LOP node happened before the layer muting
- fixed a bug that multiple USD work layers could get created in Maya
- fixed a bug that the product name of an USD export state in Maya wasn't saved in some cases
- fixed a warning when exporting.ma/.mb files using the USD Export state in Maya
- fixed a bug that USD sublayers were not added to departmentlayers automatically
- fixed some errors when submitting USD render jobs from Prism standalone
- fixed some problems with the camera menu in the USD viewport
- fixed a bug that the AOV folder had an incorrect name when rendering renderlayers in a Maya job on Deadline
- fixed an error when opening Nuke scripts with Write nodes in some cases
- fixed a bug that the After Effects plugin only loaded in the AE developer mode
- fixed a bug that the After Effects integration couldn't get removed cleanly
- fixed a bug that Prism windows were not parented to the Substance Painter window in some cases
- fixed an error when clicking the version override button in the Render window in Unreal Engine
- fixed a crash when opening the Project Browser in Unreal Engine in some cases
- fixed a bug that the context setting was hidden in the Unreal Render window in some cases
- fixed a bug that the latest scenefile version was not displayed at the top in the Project Browser in some cases
- fixed a bug that notes were not displayed for media versions in some cases
- fixed a bug that opening Shotgrid from the tasks tab in the Project Browser opened an invalid webpage
- fixed a bug that the formatting of dates in the Products tab couldn't be changed using an env var

## Prism 2.0.14

- added support for Houdini QT6 builds (which enables using Karma XPU in Prism Standalone)
- added support for opening USD files in ShapeFX Loki
- added option to setup shots in Houdini from the tab menu
- added several improvements to the Solaris multi shot workflow in Houdini
- added several improvements to the USD layer workflow in Maya
- added support for "deep alpha only exr" mode in Houdini when rendering with 3Delight
- added option to load RV annotations by clicking on attachments of notes in RV
- added option to clear the config cache when refreshing the Project Browser
- added support for displaying attachments of Kitsu notes
- added option to automatically create overrides when linking collections in Blender
- added support for displaying mono exr channels in the Media preview
- added support for selecting studio users when assigning a task using the Prism Project Manager
- added support for project presets in the studio location (in the presets/projects folder)
- added option to use short task type names from Kitsu tasks
- added an empty scene preset for Cinema 4D
- added various env vars to set Deadline pools and groups for cleanup jobs, scene description render job and master update jobs
- added a PRISM\_EPISODE environment variable when episodes are enabled in the project settings
- added env var "PRISM\_UNREAL\_USE\_HANDLES" to control if Unreal imports shots with handles
- added env var "PRISM\_SCENEFILE\_PRESET\_PATHS" to define paths where Prism looks for scenefile presets
- fixed an error when changing the task preset order for shots in the project settings
- fixed a bug that the outputpath of shotcams was incorrect when using episodes
- fixed a bug that additional export locations within the main project folder had some problems when using custom folder structure templates
- fixed a bug that the renderoutputpath of Houdini renders was incorrect when a custom output entity was selected and media identifiers were linked to tasks
- fixed a bug that state presets are not applied to the USD export shelf tool in Maya
- fixed a bug that some Maya Deadline renders had an unnecessary dot in their filename
- fixed a bug that Maya VRay renders saved AOVs in the wrong folder in recent VRay versions
- fixed an error when sending products to Blender in other formats than objs
- fixed a bug that filepaths in Nuke Read nodes could be replaced with an expression in some cases
- fixed a problem that Nuke jobs on Deadline didn't report progress
- fixed a bug that dropping geometry files in Nuke created a Read node instead of a ReadGeo node
- fixed a bug that the outputpath of Nuke Deadline jobs wasn't added to the job settings when relative paths were enabled
- fixed an error when importing products into 3ds Max in some cases
- fixed an error when importing shots into the Unreal Sequencer in Unreal 5.5
- fixed an error when importing an asset from a library into Unreal
- fixed an error when connecting a project, with episodes disabled to a Kitsu project with episodes
- fixed a problem that assigned Kitsu tasks for users with no last name were not displayed

## Prism 2.0.13

- added Cinema 4D as free open source plugin (previously available as early access for Prism Pro Users)
- added early access plugin for Adobe After Effects (currently for Prism Pro users only)
- added support for Unreal Engine 5.5
- added option to add a slate frame in the Media Converter
- added option to add image burn-ins in the Media Converter
- added support for rendering hipfiles with Prism HDAs on workstations, which don't have Prism installed (removes the license requirement for Solaris jobs)
- added support for rendering USD Standalone Deadline jobs without a Prism license
- added options to drive the Prism Import LOP using Context Options
- added an option to not use the Geometry Sequence LOP for filesequences in the Prism Import LOP in Solaris
- added option to expand attachments in notes of product/media versions to full size
- added options to the Nuke read node to browse media from the Prism project
- added Prism render options to the default Nuke Write node
- added support for submitting Nuke renders as previous versions to Deadline
- added option to enable/disable the WritePrism node in Nuke
- added option to create a Read node from a Write and WritePrism node in Nuke
- added option to set studio wide environment variables in the Studio Settings
- added support for loading single file plugins automatically from the project plugin folder
- added support for automatic viewport thumbnails when saving scenefiles in 3ds Max
- added support for creating episodes from Resolve
- added option to use clipnames as shotnames in Resolve
- added option to publish media directly to Shotgrid/ftrack/Kitsu when creating shots in Resolve
- added time meta data to USD departmentlayers by default
- added option "Set automatic time meta data" for USD files in the Product Browser
- added support for showing.mtlx files as text from the Library
- added Save Style options on the Filecache LOP
- added PRISM\_USD\_EDITOR\_SHOW\_VIEWPORT env var to be able to disable the USD viewport in the Prism USD Editor
- added PRISM\_MAYA\_WORKSPACE\_TEMPLATE env var to define a Maya project workspace template file
- enabled "Sublayer versions in USD master files" by default for all new projects
- Houdini COPs are now exported to the Library
- simplified the UI for submitting USD renderjobs to Deadline using the Prism LOP Render node
- simplied the Resolve integration. It's not needed to paste a code snippet into the Resolve console in some cases
- fixed a bug that the sequence USD layer was created in a wrong folder when episodes were enabled
- fixed an error when using presets for the texture export in Substance Painter 10.1
- fixed a bug that files rendered in Maya on Deadline had a wrong framepadding in their name
- fixed a bug that opening a sequence in the file explorer opened the wrong folder
- fixed a bug that the comment of Nuke scenefiles was cleared after rendering
- fixed a bug that the Nuke scenefile was saved twice during a Deadline submission in some cases
- fixed a bug that dragging a media version from the Project Browser into Nuke could create an unwanted read node for json files or didn't detect framesequences in some cases
- fixed a bug that the previous filepath knob on the WritePrism node in Nuke wasn't saved when reopening the scene
- fixed a bug that node errors on the ROP inside of the Prism Filecache LOP were not shown correctly to the user
- fixed a problem that USD department layers could become unmuted in Solaris after executing the Filecache LOP in some cases
- fixed a bug that the sublayer name in the USD export state in Maya was reset when reloading the scenefile
- fixed problems with the Shotgrid connection in some cases (by updating the shotgun\_api3 module to 3.6.2)
- fixed a bug that assets and shots could be created multiple times in Shotgrid/ftrack/Kitsu
- fixed some bugs in the Assigned Tasks tab when using ftrack and the "Use firstname/lastname as username" option is disabled
- fixed an error when using Kitsu sequence tasks in some cases
- fixed a bug that archived Kitsu assets and shots were displayed in Prism
- fixed a bug when publishing media with custom names from Resolve to Shotgrid
- fixed a problem that Blender and DaVinci Resolve crashed when the Autodesk identity was used for the Shotgrid login
- fixed a bug that scenefile items could appear empty in the Project Browser in some cases
- fixed a bug that items in the DependencyViewer could be displayed multiple times in some cases
- fixed an error when importing images into Photoshop
- fixed a bug that switching the version of linked collections in Blender deleted and relinked the collection instead of just updating the library path
- fixed an error when exporting usdc files in Blender when no timeline panel was visible

## Prism 2.0.12

- added support for Substance Painter v10.1.0
- added option to import connected assets into a shot scenefile to the context menu of the import button in the State Manager
- added new arguments to the installer when doing a silent install: username, password, accesstoken
- added option to select an asset or shot to render to in the ImageRender state in Houdini
- added option to drag&drop assets into the StageManager LOP in Houdini
- added option to render or submit all or all renderable renderlayers in a Maya scene
- added option to import USD files as references in Maya
- added support for removing unkown plugins when publishing Maya files
- added option to set a version override on the ImageRender state
- added option to export USD files in Blender as department USD layers
- added support to export and import.ass files in C4D
- added option to attach all annotated frames from OpenRV to a note
- added option to open the Project Browser from the Prism menu in OpenRV
- added option to refresh media playlists to the context menu of the playlist widget
- added support for casting a Kitsu asset multiple times to a shot
- added support for using entity meta data in the Media Converter Burn-Ins
- a "Textures" folder will be created now for every newly created asset
- the Nuke WritePrism node uses now the current taskname as default identifier
- fixed a bug that the project settings were not refreshed in the "Create Project" dialog when selecting a project to use the settings from in some cases
- fixed a bug that the connection settings were empty when creating a new project based on a Shotgrid/ftrack/Kitsu project when loading a project preset
- fixed an error when importing USD objects as Maya data in some cases
- fixed an error when adding objects to the export list in Blender 4.0
- fixed an error when capturing thumbnail ins the Houdini nodegraph
- fixed an error when adding a sequence in the "Create Shots" window in Resolve when no media exists in the timeline
- fixed a problem that alembic animations always started at frame 0 in the USD viewport
- fixed an error when applying an Alembic cache in Maya to assets, which contain objects with identical names
- fixed a bug that the "Copy path for next version" in the Media Browser didn't work correctly when media versions were linked to tasks
- fixed an error when creating a Shotgrid sequence under an episode
- fixed an error when none of the assigned Shotgrid tasks are on asset or shot entities
- fixed an error when creating an asset in Shotgrid/ftrack/Kitsu
- fixed a bug that changing handles to 0 in ftrack didn't sync to Prism
- fixed a bug that the sync departments button in the Kitsu settings didn't work
- fixed an error when adding Kitsu replies to notes in some cases
- fixed some bugs with the media conversion submitted to Deadline from Nuke
- fixed a bug that the Project Browser could open when rendering Cinema4D jobs on Deadline

## Prism 2.0.11

- added support for Episodes (works also in combination with Shotgrid, ftrack and Kitsu)
- added option to create and edit hooks from within the Project Settings
- added support for drag&drop images in Houdini 20.5 COPs
- added support for rendering out COP networks in Houdini with the ImageRender state
- added support to submit Shotgrid/ftrack/Kitsu publish jobs to Deadline
- added support for publishing annotations from OpenRV to ftrack and Shotgrid
- added option to sync ftrack ReviewSessions to Prisms Media Playlists
- added support for exporting collections in Blender
- added support for exporting and importing RSproxies in C4D
- added support for C4D 2023
- added support for exporting and import USD files in C4D
- added option to set a name for Access Tokens
- added option to limit Access Tokens to specific license types
- added option to limit the amount of licenses, which can be acquired with a specific Access Token
- added option to set default Prism version in the launcher (enables different Prism versions per project)
- added option to edit the name and path of Prism versions in the Launcher
- added option to view products as a table when importing assets from the Library
- added support to browse all subfolders of assets and shots in the Library
- added progress indicator when copying folders
- added H264 and MPEG4 codec options to the.mov format in the MediaConverter
- added.avi format in the MediaConverter
- added "Send To" option to the export state to send products to other DCCs instantly
- added option to automatically update the version of an USD layer in an entity/departmentlayer USD when a new layer version gets published
- added support for department prefixes when choosing sublayers to mute in the Prism Mute Department LOP in Houdini
- added an "Save paths relative to output path" outputprocessor to the Prism Filecache LOP when relative paths are enabled in the Prism Project Settings -> USD
- added option to change the status for published Kitsu versions in Project Settings
- added option to not load payloads to the Prism Import LOP
- added option to rename USD layers in Maya
- added support for using env vars in pluginpaths and pluginsearchpaths
- added env var PRISM\_VERSION
- added env var "PRISM\_SKIP\_LOGIN\_WINDOW" to skip the login window
- added env var "PRISM\_FTRACK\_IGNORE\_ASSET\_FOLDERS" to ignore specific folders when syncing assets from ftrack
- added env var "PRISM\_DFT\_LOCAL\_PATH" to set the default path for local projects
- added env vars "PRISM\_HUSK\_DEADLINE\_POOL", "PRISM\_HUSK\_DEADLINE\_2ND\_POOL" and "PRISM\_HUSK\_DEADLINE\_GROUP" to set the jobsettings for Husk renderjobs
- added env vars "PRISM\_USD\_EXPORT\_DEADLINE\_POOL", "PRISM\_USD\_EXPORT\_DEADLINE\_2ND\_POOL" and "PRISM\_USD\_EXPORT\_DEADLINE\_GROUP" to set the jobsettings for USD exportjobs
- added env var "PRISM\_SHOW\_INVALID\_VERSION\_NAMES" to show folders with custom names in the version column of the Product Browser
- improved performance of the Scenefiles tab
- improved performance of the Libraries tab
- redesigned the Maya USD export UI and added new options
- launching DCCs from the Project Browser will now set user and project env vars before launching the DCC, which is required for using OCIO in some DCCs
- the default OCIO display and view will be set in existing Houdini viewports now when Prism sets the OCIO env var
- updated the empty Houdini scenefile preset, so that it doesn't throw a warning in newer Houdini versions
- changed the "Show Media Status" to "Enable Media Publishes" and "Show Product Status" to "Enable Product Publishes" in the Project Management plugin
- when publishing videos to Shotgrid, the startframe will now get set correctly
- previews of product publishes are now upload in full resolution to Shotgrid/ftrack/Kitsu
- the revision number of Kitsu media publishes matches now the media version number in Prism
- plugin shapes are now set to visible in the recommended playblast settings in Maya (to show USD objects)
- fixed a bug when applying a media conversion after a render in Maya in some cases
- fixed an error when switching between media versions in some rare cases
- fixed a problem that media files in scenefile folders could influence the versionnumber of new scenefiles
- fixed the bug that the state of the "Format" checkbox in the Substance Painter export window didn't get saved between sessions
- fixed a bug that shots were not rendered in the correct framerange when creating new shots from within Resolve after pasting spreadsheet data
- fixed crashes when launching hython in some cases
- fixed a bug that no thumbnail was set when drag&drop products from the Product Browser into the Houdini Layout Asset Gallery
- fixed a bug that the version number on the Prism LOP Render node was not used for Deadline jobs
- fixed a bug that no camera could be selected when trying to render a USD turntable
- fixed a bug when exporting USD layers from Maya that an irrelevant framerange warning could show up in some cases
- fixed a Maya crash when exporting a USD file when the object hierarchy starts with `"|world"`
- fixed a bug that an unwanted USD export job was submitted when submitting Solaris renders in some cases
- fixed a bug that the USD export of the LOP Render node could be saved as a wrong version in some cases
- fixed a bug that the department of the Filecache sublayer was reset when opening scenefiles from the standalone Project Browser
- fixed an error when trying to download QuiltiX
- fixed a bug when launching DCCs from the Launcher when the pipeline folder had a non-default name
- fixed an error when opening the Launcher when no project is active
- fixed an error when converting long exr sequences with the Media Converter and text overlays
- fixed a bug that the thumbnail of some Library items didn't refresh when resizing the window
- fixed a bug that the code state in 3ds Max could cause an error in some cases
- fixed a bug that material settings of fbx import in Unreal weren't saved between imports
- fixed an error when uninstalling individual plugins
- fixed an error when exporting objects in Blender while not in object mode
- fixed an error in Blender when exporting an abc and the usda sublayer master versions are enabled
- fixed a bug that Blender playblasts could use the wrong viewlayer in some cases

## Prism 2.0.10

- added new plugin Cinema4D (early access)
- added option to automatically create scenefiles from a preset when a task gets created
- added option to sync studio users from Shotgrid, ftrack and Kitsu, including their roles and assigned projects
- added option to sync asset-shot links from Kitsu
- added support for using EXR meta data as burnins in the Media Converter
- all plugins in the default plugin path will be loaded now (no need to add them in the user settings anymore)
- the "Show previews" checkbox in the Resolve "Create Shots" window is now unchecked by default
- the USD turntable tool is now available for all Prism Plus users
- fixed a bug that the prim hierarchy was wrong when exporting multiple objects from Maya, which were pulled from a USD stage, as USD
- fixed an error when rendering multiple level sequences in Unreal after each other in some cases
- fixed an error when opening the export window in Unreal when having an empty section on a Subsequence track in a Level Sequence
- fixed a bug that importing multiple instances of an asset at once didn't work in some cases
- fixed an error when copying settings from the Media Converter while being in "Edit Preset" mode
- fixed a bug when creating MaterialX files from exported textures in Substance Painter
- fixed a bug that the source media was not added to published ftrack versions
- fixed a bug when publishing mp4 files directly from the State Manager to Kitsu
- fixed a bug that media was imported into Nuke with absolute paths even if relative paths were enabled in the Prism User Settings
- fixed a bug that the media conversion in Nuke didn't work when using relative paths
- fixed a bug when saving multi-layer-exr files using compositing nodes in Blender

## Prism 2.0.9

- added option to import media as camera backplate or domelight texture in Houdini and Maya
- added option to the Project Settings to set a project specific launcher config
- added option to drag&drop assets into the Houdini Asset Gallery Pane and into the Parameters pane of Layout LOP nodes
- added option to show recent projects to the artists when the Studio plugin is active
- added option to toggle the autoload of multiple plugins at once
- added option to specify authentication for Shotgrid, ftrack and Kitsu using env vars
- added option to mute department sublayers from the Mute Departments HDA in Solaris
- added confirmation popup when removing a project from studio settings
- updated the gazu module of the Kitsu plugin
- changed the Maya integration to use a module file instead of the userSetup.py in the Maya user preferences
- mov files get uploaded now directly to ftrack on publish without a local conversion
- improved the download progress indicator in the Hub
- fixed a bug that prevented Prism from loading in OpenRV
- fixed a bug that could cause crashes when loading hipfiles with playblast states in some cases
- fixed a bug that the camera menu of the USD viewport wasn't refreshed when changing the USD stage
- fixed a bug that could show the same department multiple times in the USD layer order
- fixed a bug that the Mute Department HDA could mute sequence layers instead of shot department layers
- fixed a bug that caches in Houdini were considered to be part of wedges in some cases
- fixed an error after rendering in Nuke when Prism was connected to a Project Management tool
- fixed several problems with nogui installations

## Prism 2.0.8

- added option to specify location, department and task when creating products and productversions in the Project Browser
- added option to create departments on multiple assets/shots at once
- added option to exclude frames using "^" in framerange expressions
- added options to export USD layers from the Prism Filecache SOP in Houdini
- added options to open the FBX export settings from the Export state settings in Maya
- added option to import fbx files as control rig into the Unreal Sequencer
- added option to set the Kind of USD prims in the USD Editor
- added support for shothandles from ftrack
- fixed an error when opening the Ingest Media tool, when media versions were linked the departments and tasks
- fixed a bug that the Prism LOP import node caused some unexpected behavior when using scale and layerbreak options
- fixed an error when creating a LOP node network for the current department
- fixed an error when browsing products from the LOP import node in some cases
- fixed some bugs when importing lighting presets in LOPs
- fixed a bug that the framepadding setting in the Project Settings wasn't used in all places in Houdini
- fixed a bug when drag&drop images in Redshift Material networks in Houdini Solaris
- fixed a bug that viewing the text of a USD file from the Project Browser showed the flattened stage instead of only the layer
- fixed a bug that sequence USD layers were always added with absolute paths to shot USD files
- fixed a bug when syncing shothandles from Shotgrid in some cases

## Prism 2.0.7

- added support for Unreal Engine 5.4
- added support for shot handles
- added new media ingestion tool
- added options to publish media and products directly from the State Manager to Shotgrid/ftrack/Kitsu
- added option to login/logout of Shotgrid, ftrack, Kitsu directly from the Project Browser
- added option to change the framepadding in the project settings
- added option to change the versionpadding in the project settings
- added option to set the project version in the project settings
- added option to open output folders to the "Successful Publish" popup
- added support for wedging directly within the Prism Filecache SOP node in Houdini
- added option to open exported caches in the Product Browser from the Filecache SOP in Houdini
- added support to use LOP Import Camera nodes in Playblast states in Houdini
- added option to the LOP Render node to render every x frame on Deadline
- added support for rendering the OpenGL node in Houdini
- added option to the Prism Filecache SOP and LOP to not use an expression for the read cache filepath, which improves read performance significantly
- added option to the Filecache LOP to set the Save Path on a USD layer without exporting files
- added option to the Project Browser to view usd files as text
- added option to modify USD layers in the USD Editor by editing the layer as text
- added options to the USD Editor to copy/paste layer content
- added option to the USD Editor to clear layer content
- added option to choose from existing USD sublayernames when exporting sublayers in Maya
- added support for linked departments and tasks when creating media identifiers and external media
- added option to specify a project template when creating new Substance Painter scenes
- added option to create single file plugins from the Create Plugin window
- improved behavior when launching the tray, when there are already Prism processes running
- creating USD sublayers in the Product Browser adds the sublayer automatically to the department layer now
- simplified the saving of anonymous USD layers in the USD Editor
- the scale in the Prism LOP Import node in Houdini got moved under the layer break
- fixed a bug that restarting the tray didn't work in some cases
- fixed a bug that selected shots weren't selected after refreshing the Project Browser in some cases
- fixed a bug that media playlist items didn't display thumbnails in some cases
- fixed a bug that no save reminder popup was shown in Blender when opening new scenefiles in some cases
- fixed an error when exporting usd files with Houdini Apprentice in some cases
- fixed a bug that the USD layermuting didn't work in some cases
- fixed that the first person navigation in the USD viewport didn't work since the recent USD libraries update
- fixed an error when exporting.usd files from Maya in some cases when not all parents were selected for export
- fixed a bug that colorspaces weren't loaded correctly from OCIO configs
- fixed some problems when rendering Maya Renderman jobs on Deadline
- fixed an error when using the asset search when a Project Management plugin was used

## Prism 2.0.6

- added option to send geometry with 1 click between Houdini, Maya, ZBrush and Blender
- added option to add assets from other Prism projects as a library to the current project
- added option to setup entity departments in Solaris using drag&drop from the library
- added search bar to asset libraries
- added option to open USD files from the Library in Usdview
- added option to import usd, abc, fbx and obj files from the project library and custom libraries
- added option to import models from PolyHaven into DCCs
- added support for capturing a thumbnail when saving Substance Painter scenefile versions
- added support for capturing a thumbnail when saving ZBrush scenefile versions
- added option to add custom layer names to the USD layer order in the Project Settings
- added option to reset USD turntable settings to their defaults by rightclicking on the settings
- added option to create assets in ftrack from Prism
- added option to set a prefix for Prism selection sets in Maya
- added option to change the default AOV on the Prism LOP Render node in Solaris
- added option to set the render version number on the Prism LOP Render node
- performance optimizations when refreshing the shot list
- the asset/shot search bar also checks the asset/shot description now
- the USD sublayer position in department layers gets preserved now when publishing new sublayer versions
- improved the published ftrack version naming by string the version number to match how ftrack names manual publishes
- fixed some problems when publishing products to ftrack
- improved the auto-positioning and framing of the asset in the USD turntable tool
- for scenefiles, which don't have meta data saved with them, the filename will be used as the comment in the Scenefiles tab
- fixed a bug when adding objects to an export state in Maya in some cases
- fixed an error when opening Houdini in some cases
- fixed an error when publishing the component builder in Solaris when the Variant Layers are enabled
- fixed an error when dragging a usd file from the Library into Solaris and loading it as a layer
- fixed an error when trying to assign a user to a project in the studio settings
- fixed a bug which could cause warnings in some cases when switching projects when the Shotgrid/ftrack/Kitsu server changed
- fixed an error when updating imported USD files in Maya in some cases
- fixed a bug that Deadline cleanup job could fail in some cases if spaces where in the filepath
- fixed an error when exporting Substance Painter textures to an unmapped network drive with a custom export preset, which includes subfolders
- fixed a bug which could cause crashes in some cases when the USD viewport was visible when opening the Project Browser
- fixed a bug that the USD turntable animation had an offset if the usd file had a fps other than 24
- fixed a bug when toggling the color reference in the USD turntable tool when relative paths are enabled in the project settings

## Prism 2.0.5

- added option to import assets from the Library window instead of the Product Browser
- added new menubar to the USD viewport (based on Usdview options)
- added turntable tool with various settings to design turntables of USD assets
- added option to import connected assets into shot scenefiles in Houdini and Maya
- added option to import.usdz files
- added option to convert alembic to USD files
- added option to load multiple departments of an asset/shot into Houdini Solaris (WIP)
- added support for Maya 2025
- added support for 3ds Max 2025
- added option to import.abc,.fbx and.obj geometry into Nuke
- added option to import.abc and.fbx cameras into Nuke
- added support for automatic media conversion after Nuke renders and Deadline submissions
- added option to create playblasts with audio from Blender
- added option to create a new Prism project from existing Shotgrid/ftrack/Kitsu projects
- added ftrack/Kitsu login window when loading a project and the login credentials are not set in the Prism User Settings
- added option to add a description and preview images for Shotgrid/ftrack/Kitsu product publishes
- added support for sequence tasks from Kitsu
- added option to create assets from Prism in Kitsu
- added option to create shots from Prism in Kitsu
- added option to use filenames as ftrack version names
- added option to create local folders for all Shotgrid/ftrack/Kitsu entities
- added option to update imported assets in Unreal to their latest version
- added option to import USD files in ZBrush
- added option to export.usda and.usdc files from ZBrush
- added option to not save the current scene before a publish
- added option to not save the current scene during a publish
- added option to refresh the whole Prism Hub
- added support for.m4v videos
- added option to remember widget sizes in the Project Browser
- added reminder to install ProjectManagement plugin when installing the Shotgrid/FTrack/Kitsu plugins
- added support for relative outputpaths in Nuke
- added option to generate a MaterialX file from exported textures in Substance Painter and assign the material to an USD asset
- added option to automatically download QuiltiX
- added option to select and open product versions in QuiltiX
- added option to save MaterialX files from QuiltiX as product versions
- added env var "PRISM\_BLACKLISTED\_EXTENSIONS" to define fileextensions, which Prism will ignore
- added option to set subframes on the Prism LOPs Filecache node in Houdini
- added option to set if the texture master version should be updated when exporting textures from Substance Painter
- added support for saving previously used settings in the texture export window in Substance Painter
- added option to open the Prism Discord Server directly from the Project Browser
- updated Prism Standalone to Python 3.11
- updated the USD libraries to v24.03
- when importing USD files into Maya downstream departments are now muted in the Maya USD Layer Editor
- opening a Houdini scene, which contains Prism LOP nodes, when the Prism USD plugin is not loaded doesn't cause errors anymore
- opening or loading a Maya scene will now set the USD Edit Target to the current department layer
- choosing to not add a project to the studio settings will be remembered now
- fixed a bug that the thumbnail of some exr files couldn't be loaded
- fixed a bug that opening files in the file explorer from the Dependency Viewer opened wrong files in some cases
- fixed a bug that scenefile descriptions were carried over to the next versions
- fixed a bug that linking external media in the Media tab didn't work correctly
- fixed a bug that for some image ftrack publishes a too small, unnecessary thumbnail was generated
- fixed a problem with the encoding of published media to ftrack
- fixed a bug that exporting.fbx files from the Prism Filecache SOP in Houdini produced non readable files in some cases
- fixed a bug that the "Copy path for next version" feature created a json file with an incorrect name
- fixed a problem with wrong filenames when submitting Blender single frame jobs to Deadline
- fixed a bug that updating Nuke Read nodes with env vars in the filepath didn't work
- fixed a problem that only a single UDIM could be exported from Substance Painter when using an export preset
- fixed a bug that colorspaces in MediaConverter presets weren't loaded correctly
- fixed a bug that Resolve renders had an invalid department/task in the paths when the option to group media versions in departments/tasks was enabled
- fixed a problem that the GPU Open MaterialX library was broken, because the URL was changed
- fixed a bug that selecting USD reference files in the USD Editor from the Product Browser didn't work
- fixed a bug that MaterialX materials were not displayed in Prism Standalone in some cases
- fixed a bug that the USD viewport toggle was reset when minimizing and restoring the Project Browser
- fixed a bug when using relative paths for references in the USD Editor
- fixed a bug that the standalone USD render didn't use the resolution from the rendersettings prim if the resolution override was disabled

## Prism 2.0.4

- added task presets (like "Character", "Prop"...) to automatically create tasks at asset/shot creation
- added new Maya shelf tools as an alternative to the State Manager (requires to add Prism Maya integration again)
- added option to import.nk files into Nuke
- added option to export.nk files from Nuke
- added option to add an exported Maya scene as a reference prim to a USD stage
- added support to create ImageRender states for multiple ROPs at once in Houdini
- added option to not use the outputformat override for Arnold renders in Houdini
- added support for "albedo" textures when dragging textures into Houdini and generating materials automatically
- added option to regenerate thumbnails in the Library
- added option to set an expected project path in the project settings to prevent problems when users load a project from different paths
- added ocio env var to husk render jobs
- improved support for PySide6
- improved error handling when saving USD stages
- setting the studio path doesn't ask now anymore if the studio config should get reset
- the default USD product for new assets gets created now with a default variant
- fixed a bug that USD sublayers with underscores in their names were not displayed correctly in the product list in the Project Browser
- fixed a bug that the default USD structure of assets converted the assetname to lowercase
- fixed export and import of Shotcams when products are linked to departments and tasks
- fixed a bug that the dependencies window didn't refresh in some cases
- fixed a bug that publishing products/media to Shotgrid used the product/identifier name to find the matching SG task even if products and media were linked to tasks
- fixed a bug that deepexrs were changed to normal exrs when rendering with Arnold in Houdini
- fixed a bug that Blender scenes couldn't be loaded from unmapped network paths
- fixed an error when setting set fps in Blender in some cases
- fixed a problem when opening the Blender integration setup window in some cases
- fixed a bug that Deadline jobs were not grouped in some cases

## Prism 2.0.3

- added option to link products and media to departments and tasks
- added support for the Autodesk Identity login for Shotgrid, which supports 2FA
- added option to create Shotgrid assets and shots from within Prism
- added option to use asset/shot specific resolutions and fps
- added option which textures to export from Substance Painter when using export presets
- added option to not override the fileformat when exporting textures from Substance Painter when using export presets
- added option to save Houdini nodegraph presets to custom locations
- added option to create USD department layers automatically when departments are created in the Scenefiles tab
- added option to export Houdini scene descriptions locally before rendering them on Deadline
- added option to set an admin password for the studio settings, which can be used to enable an admin mode with full permissions
- added support for float fps values in Blender
- added option to enforce OCIO in Nuke
- added option to choose if the ftrack username or firstname/lastname will be used as the Prism username
- added option to apply abc caches to specific assets in the current Maya scene
- opening and saving Maya scenefiles will now be added to the Maya Recent menu
- after exporting USD layers from Maya, the old layers will be replaced with the newly exported layer in the Maya USD Layer Editor
- when importing an entity USD file into Maya, the Edit Target will be set to the layer which matches the department of the current scenefile
- the default product for assets in the Library is now "USD" and can be set using the "default" tag on products
- fixed an error when using RGBA\_\* for aovs in Houdini with Arnold
- fixed a bug that some Python API functions could freeze Houdini when called from Python TOPs
- fixed a bug that import textures in Houdini used "%(udim)d" instead of the correct "<udim>" tag
- fixed some problems with tile rendering in 3ds Max
- fixed a crash when opening Houdini scenes with the Prism LOP Render HDA in some rare cases
- fixed a problem that writing USD files from Blender to network drives could cause errors
- fixed a crash when exporting.blend files in Blender 4
- fixed a problem that the Project Management plugin could change the Prism username to the Shotgrid/ftrack/Kitsu username, which could result in loosing all permissions, when the Studio plugin was active
- fixed a bug that it was not possible to connect assets to shots when the studio plugin was active

## Prism 2.0.2

- added option to reference in USD files using the Prism Import LOP in Houdini
- added option to not add meta data in the Prism Import LOP in Houdini
- added option to specify locations of custom Houdini nodegraph presets using the "PRISM\_HOUDINI\_NODEGRAHPRESET\_LOCATIONS" env var
- added option to open QuiltiX from the Project Browser menus
- ftrack episodes are now synced to Prism when the "PRISM\_USE\_SEQUENCE\_FOLDERS" env var is set
- opening media files from the library uses now the media player, which is configured in the Prism User Settings
- the USD viewport is now hidden by default in Nuke 15 to avoid crashes on startup in some cases
- fixed an error when creating new projects in some cases
- fixed an error when rightclicking the Usd viewport in the Project Browser
- fixed a bug that in some cases the default executable for filetypes wasn't detected correctly
- fixed a bug that unomitting assets didn't work in some cases
- fixed a bug that publish warnings were shown in Maya for filepaths with copy numbers
- fixed an error when linking or appending.blend files in Blender in some cases
- fixed multiple problems with 3dsMax Redshift tile rendering on Deadline
- fixed a bug that products exported with the USD Export state in Houdini were added to the entity USD even if the mode wasn't set to "Layer"

## Prism 2.0.1

- added option to create ftrack shots from within Prism
- added option to disable the script dependecies of Deadline scene description jobs and use job dependencies instead
- added support for environment variables in executable override paths
- added option to add command line arguments to the media player executable
- added support for submitting Vray standalone renderjobs from Houdini to Deadline
- added option to remove existing OCIO env var in the Media category of the Project Settings
- added option to sublayer versioned usd files in master files to avoid permission errors
- added options to load custom Usd Stage presets into the Prism Usd Viewport
- added support for updating USD layers on Deadline using the Prism Filecache LOP
- added option to export Arnold.ass files from Maya
- added option to save ZBrush scenefiles as.ztl files
- added options to select which maps to export from ZBrush
- added option to set texture resolution when exporting textures from ZBrush
- added option to display multiple levels of folders for shots in the Project Browser (for example for episodes) using the "PRISM\_USE\_SEQUENCE\_FOLDERS" env var
- added support for setting a preferred license type using the env var "PRISM\_PREFERRED\_LICENSE\_TYPE" or in the license json file
- simplified accessing Prism in Resolve Studio
- fixed a bug that in some cases textures of the first subtool in ZBrush wasn't exported
- 3dsMax Deadline jobs will now ignore missing DLL files
- fixed an error when loading previews in the Resolve Create Shots window in some cases
- fixed a bug that some processes couldn't be started from UNC paths
- fixed a bug that default foldertemplates were used in some cases when the default project pipeline folder was changed
- fixed a bug that 3dsMax Deadline jobs rendered the wrong camera when the renderview was locked
- fixed an error in Blender 4.0 when saving scenes in some cases
- fixed a bug that env vars defined in the Launcher didn't get evaluated in some cases
- fixed an error when switching the framerange of an ImageRender state to "Expression" in Houdini
- fixed a bug that the Prism Import LOP in Houdini didn't display all asset info if relative paths were used

## Prism 2.0.0

## Prism 2.0.0.beta17.15

- fixed a bug that Prism could freeze when opening the Prism Settings in some cases
- fixed a bug which causes Blender to crash when opening scenefiles in some Blender versions
- fixed an error when submitting a media conversion job to Deadline from some DCCs
- fixed a bug that double clicking a task in the "Create Task" window closed the window without creating the task
- fixed a bug that local product versions were not displayed in the Project Browser in some cases

## Prism 2.0.0.beta17.14

- added default department icons
- added support for Blender 4.0
- added option to import asset products more easily from the Asset Library
- added option to set the count of a product to be imported from the asset library using ctrl + left/right clicks
- added support for skipping the auto load of plugins defined by the env var "PRISM\_IGNORE\_AUTOLOAD\_PLUGINS"
- added an "onLauncherDetectApps" callback
- improved asset creation window
- departments are now displayed with their full name in the Project Browser
- ZBrush texture maps get exported only from visible subtools now
- fixed an error when trying to uninstall plugins
- fixed a bug that some warnings could show up in the Houdini console when launching Houdini from Prism standalone with the "Open scenes in manual update mode" option enabled
- fixed some compatibility problems with 3dsMax 2024.1
- fixed a bug that setting applying the project resolution in 3dsMax didn't work correctly
- fixed a bug that the State Manager didn't remember the selected camera in ImageRender states in 3dsMax
- fixed a bug that 3dsMax tile rendering on Deadline didn't handle AOVs correctly
- fixed a bug when exporting ZBrush textures from assets inside of assetfolders

## Prism 2.0.0.beta17.13

- added options to add sequence USD files to shot USD files
- added commandline arguments to the installer, which allow a silent install
- added option to install the Hub from within Prism
- added support for Python 3.11
- added option for Deadline tile rendering in 3dsMax
- added support for thumbnails when saving versions of Photoshop scenefiles
- added option to specify paths for additional Houdini HDAs in the Studio settings
- added option to specify paths for additional Python modules in the Studio settings
- added support for using variables like $OS in product and identifier names in the Prism Houdini Filecache SOP/LOP and LOP Render HDAs
- improvements to the shot import into Solaris
- changed the udim variable in filepaths from "%(UDIM)d" to "<udim>" when drag&dropping textures into Solaris, which is supported by more renderers
- exporting textures from ZBrush will now export a texture per subtool and merge it together afterwards
- fixed a bug that the "Other" scenefile filter wasn't working
- fixed a bug that drag&drop textures into Houdini didn't work in subnets
- fixed a bug when drag&drop textures in Houdini that the signatures of MaterialX texture nodes were not updated
- fixed a bug that launching Houdini from Prism standalone in manual update mode didn't work in some cases
- fixed a bug that prevented Prism from using Blender Compositing nodes for AOVs
- fixed an error when having an ftrack task assigned, which doesn't belong to any asset or shot
- fixed wrong filenames of textures exported from ZBrush

## Prism 2.0.0.beta17.12

- added option to download the installer and plugins as.exe and.zip from the Prism Hub
- added an indicator when the scenefile filter is active
- added support for drag&drop various image file formats into the USD viewport to use the file as a dome light
- added option to lower the bitdepth when exporting 32bit images from Photoshop to jpg
- added support for.png and.exr playblasts in Houdini
- added support for Arnold deep exr files in Houdini /out
- added option to submit an.rs export and a dependent Redshift standalone render job from 3dsMax to Deadline
- added option to navigate the states in the State Manager using the up and down arrow keys
- added env var PRISM\_LAUNCHER\_SHOW\_CENTRAL to open the Launcher at the center of the screen (in cases where the Windows taskbar is moved and the default Launcher position isn't ideal)
- renamed the "TextureLibrary plugin to "Libraries" because it already supports more than textures and will do even more in the future
- moved the querying of exr layers in a separate thread, which improves interactivity with very big exr files
- exporting fbx files from Maya will not ask or delete out-of-range keyframes anymore. This can be controlled now using the PRISM\_MAYA\_FBX\_DELETE\_OOR\_KEYFRAMES env var
- if the Arnold Layer Name for AOVs is disabled in Houdini, Prism will fallback to the AOV variable name
- fixed some bugs that the rendered framerange in 3dsMax was incorrect in some cases
- fixed a bug that the camera override in the playblast state in Houdini didn't work in Solaris
- fixed a problem that some default ZBrush shortcuts were broken after adding the Prism integration
- fixed an error when loading media files in the Media Converter, which are located under a shot folder, but were not created by Prism
- fixed a bug that wrong previewfiles were cleaned up in some cases when publishing media to Kitsu, Shotgrid or ftrack
- fixed a bug that the Prism login window opened in some cases where a workstation hasn't been used for a while although an access token was set in a license file

## Prism 2.0.0.beta17.11

- added support for Unreal 5.3
- added support for importing vdb files in Unreal 5.3
- added option to select which cameras to export from an Unreal Engine Level Sequence
- added option to restart the Prism Tray
- added option to choose whether Arnold AOVs in Houdini should be saved as separate files or in a multi channel exr
- added option to use short department names from Shotgrid
- Maya objects are now exported in worldspace to USD if the parents are not included in the export
- improvements to the USD and shot import in Unreal Engine
- improved auto-detection of Blender installations
- regenerating thumbnail in the Media preview clears all the thumbnails of a filesequence now instead of just the current frame
- fixed a bug that playblasts in Houdini were created with a wrong gamma in some cases
- fixed a bug that doubleclicking a department in the "Create Department" dialog didn't create the department
- fixed an error when adding AOVs to Houdini render states in the State Manager
- fixed a bug that Nuke was launched with a different environment when launched in a non-default mode like NukeX or Nuke Indie
- fixed a bug that the update button in the Update Master window disappeared in some cases
- fixed a problem that the Unreal Engine Editor couldn't be started from the Prject Browser in some cases
- fixed a bug that objects in Maya were selected after an fbx export, which was visible in following playblasts

## Prism 2.0.0.beta17.10

- added options to increment shot and sequence names in the Create Shot window
- added option to rename states in the State Manager
- added option to delete product versions for studio users
- added option to delete media versions for studio users
- added support for exporting and rendering Arnold.ass files on Deadline submitted from Houdini
- added support for viewing multi-image exr files in the media preview
- added option to export fbx cameras from Unreal Engine
- added option to import fbx animations and fbx rigs automatically into the Unreal Sequencer
- added option to sort by column and update selected master versions in the "Master Version Manager"
- enabled the "Flatten SOP Layers" option on the USD Render ROP inside of the Prism LOP Render node in Houdini
- fixed a bug that the Media Converter didn't detect filesequences when using the "Browse File" dialog
- fixed a bug that Prism didn't close exr files after reading their channels for the media preview, which caused that the files couldn't be deleted unless Prism was closed
- fixed a bug that Houdini Prism import nodes loaded only a single frame of filesequences
- fixed a bug that the uninstaller didn't remove the Prism installation folder in some cases

## Prism 2.0.0.beta17.9

- added support for saving scenefiles, products and media on sequence level
- added option to flatten asset folders in the Library tab
- added support for displaying textures from custom export locations in the texture library
- added option to rename sequences
- added option to match product/media version numbers to scenefile numbers
- added option to sort states in the State Manager based on their identifier/product names
- added option to add new users automatically to the studio users with a specific role
- added option to request new users to choose a username from the existing studio user list
- added option to the Houdini Prism Import SOP to select values of the info parms
- added option to delete nodes for all states in Houdini when deleting multiple states at once
- added support for env vars PRISM\_PRODUCT\_MASTER\_LOC and PRISM\_MEDIA\_MASTER\_LOC to force a specific location for master versions
- added warnings when trying to load Prism in Python 2 versions of Maya and Nuke
- importing a USD file to a new stage in Maya opens the file as a stage now instead of adding it as a layer to an anonymous stage
- media version locations are now displayed as suffix in the media version list
- fixed a bug that only a single file of a product filesequence was imported in Houdini
- fixed a bug that the shot search filter was case sensitive
- fixed an error when opening the USD viewport in Nuke 14.1
- fixed an error when checking the latest master versions for products and media in some cases
- fixed an error when copying Poly Haven assets to the active Prism project
- fixed an error when opening the Assign Users window in the Studio settings in some cases

## Prism 2.0.0.beta17.8

- added option to export specific layers from USD stages in Maya
- added option to set the department for which a USD export in Maya will create a department layer
- added option to import USD files into new or existing USD stages in Maya
- added option to view assigned materials in the Prism USD Editor
- added option to unbind assigned materials in the Prism USD Editor
- added option to filter stable Prism versions in the Hub
- improvements to the "Update Available" window with a description of changes and link to the full changelog
- fixed an error when rightclicking product groups when the USD plugin was loaded
- fixed a problem when trying to open files with their default application in some cases
- fixed an error when disabling the Kitsu/Shotgrid/ftrack plugin if it's the currently active Project Manager in the current project
- fixed a bug that doubleclicking a psd file in the standalone Project Browser opened Photoshop without opening the psd file
- fixed a bug that Prism didn't load in Houdini <19.5.379

## Prism 2.0.0.beta17.7

- added support for grouping products in the Project Browser
- added support for exporting maps from ZBrush
- added option to export files from ZBrush to assets/shots other than the one in which the current scene is saved
- added option to set the position of burn-ins in relative to the image size in the media converter
- added option to set the text font for burn-ins in the media converter
- added support for importing USD and other filetypes besides.max,.abc and.fbx in 3dsMax
- added support for importing cameras into Unreal from products other than ShotCams
- added an option to save Arnold AOVs in a single file by setting the env var PRISM\_HOUDINI\_ARNOLD\_SEPARATE\_AOVS to "0"
- added an option to specify if external media players can understand framepatterns (by default Prism will assume no)
- reduced the filesize of preview videos when publishing to Kitsu, Shotgrid or ftrack
- fixed an error when using the Prism USD plugin in 3dsMax when the 3dsMax USD plugin is installed
- fixed a bug that cropping and scaling videos in the media converter showed a wrong media preview
- fixed a bug in Houdini that the Arnold material output node wasn't connected when creating materials by dropping textures into the nodegraph
- fixed a bug that Arnold texture nodes in Houdini didn't work when the filename started with a number
- fixed a problem that the Houdini LOP import node loaded files as static if the "Reverse Vertex Ordering" option was enabled
- fixed an error when using the dependency state in Houdini when no Renderfarm plugin was loaded in Prism
- fixed an error when trying to open a media version in ftrack in some cases
- fixed an error in Resolve when loading thumbnails from video clips in the "Create Shots" window
- fixed a bug that could cause a crash when launching Maya 2022.0-2022.3

## Prism 2.0.0.beta17.6

- added entitynames to the entries in the "Recent" menu in the Project Browser
- added support for converting colorspaces between linear and sRGB with the media converter even if no OCIO is set
- added a fallback plugin install location if the default location has
- fixed a bug that the path of PolyHaven HDRIs couldn't be copied from the context menu
- fixed an error when trying to export floating point textures in Substance Painter
- fixed a bug that the Hub didn't display a warning popup if a plugin couldn't be installed
- fixed a bug that it was not possible to open the Prism console from the default Prism install location
- fixed a bug, which prevented the "Render all write nodes" option in Nuke to work with the WritePrism nodes

## Prism 2.0.0.beta17.5

- added support for importing geometry in Substance Painter from Windows network paths
- added support for exporting textures from Substance Painter to Windows network paths
- added option to add department icons
- fixed a bug that PolyHaven textures couldn't be downloaded in different resolutions and dragged into Houdini
- fixed an error when saving Resolve projects in some cases
- fixed an error when importing AOVs as a Nuke layout
- fixed an error in Unreal when exporting Level Sequences as.fbx in UE 5.2

## Prism 2.0.0.beta17.4

- added propper support for saving, loading and versioning DaVinci Resolve projects in the Prism Project Browser
- added option in the Media Converter to add multiple modifiers of the same type in the "Edit Preset" mode
- added option to lock the aspect ratio for the resolution override for Photoshop exports
- fixed a bug that the media converter used always the project FPS for video conversions
- fixed an error when querying published versions from Kitsu in some cases
- fixed a bug that projects, which were created while an existing Prism 1 project was active, used yml files instead of json files
- fixed a bug that the camera dropdown in the USD viewport toolbar didn't work
- fixed an error when submitting Standalone USD Render states to Deadline from Houdini
- fixed a bug that Deadline husk render jobs were always rendering using Karma
- fixed a bug that the camera resolution was reset when updating imported cameras in Houdini
- fixed a bug that that Kitsu/Shotgrid/ftrack project names were stored in project presets and applied to newly created Prism projects
- fixed an error when trying to unload a single file plugin with a customized pluginname

## Prism 2.0.0.beta17.3

- added new designed Prism Hub
- added options to launch Nuke as Indie, Assist, Studio or Non-Commerical from Prism Standalone
- added option to skip the Windows pathlength check using the env var PRISM\_IGNORE\_PATH\_LENGTH
- added a warning before rendering in Maya when there are multiple cameras set as renderable
- thumbnails gifs for FTrack media publishes are much smaller now
- fixed a bug that some textures couldn't be displayed in the USD viewport
- fixed a crash when loading video previews in some cases
- fixed an error when converting media on some computers
- fixed an error when creating new Substance Painter projects with versions before v9.0
- fixed a bug that product and media publishes to Kitsu were not displayed correctly when the asset/shot had an underscore in it's name
- fixed a bug that ImageRender states in Houdini created new ROPs when the State Manager was opened if the state wasn't connected to a valid ROP already
- fixed a bug that the Project Browser didn't open when double clicking the tray when the Launcher plugin was loaded

## Prism 2.0.0.beta17.2

- added support for importing USD files in Substance Painter
- added option to create new projects based on settings of existing projects without creating presets first
- added option to set the purpose of prims in the USD Editor
- added support for single file python plugins
- added option to update the master version when creating a playblast in Maya, 3dsMax and Blender
- added support for creating standalone USD playblasts from inside Maya
- updated the installer to make it more stable and easier to use
- simplified the project creation window
- changed the env var to set the Prism username from PRISM\_USER to PRISM\_USERNAME
- fixed a crash when reloading plugins in the user settings
- fixed a bug that master media versions in the Project Browser didn't show the correct files on disk
- fixed a bug that it was not possible to create asset folders when the studio plugin was loaded
- fixed an error when exporting usd files from Blender
- fixed a bug that textures couldn't be displayed in the USD viewport in some cases
- fixed a bug that some products couldn't be set as master versions

## Prism 2.0.0.beta17.1

- added support for viewing.fbx files in the USD viewport in Prism Standalone
- added option to set the displayed "Purpose" in the USD viewport
- added option to update master versions from Photoshop exports
- added option to open the Project Browser from the tray icon using a doubleclick while the Launcher plugin is active
- added option to set the username using the env var PRISM\_USER
- added option to set the username abbreviation using the env var PRISM\_USER\_ABBREVIATION
- opening a USD viewport closes now all existing USD viewports to avoid crashes
- the media preview slider keeps the current frame number now when switching versions and AOVs
- the "Flatten SOP Layers" option is now enabled in the Prism Filecache LOP node in Houdini
- fixed a bug that USD stitching didn't work when submitting the export job to Deadline
- fixed a bug that Prism LOPs Filecache nodes didn't read files when submitted to Deadline in some cases
- fixed an error when submitting Deadline jobs in some cases when the Media Extension plugin was enabled
- fixed a problem that the OpenImageIO (responsible for loading some texture file types) couldn't be loaded on some computers
- fixed a bug that Arnold couldn't be used in Usdview when opened from Prism
- fixed several issues with saving and loading studio settings
- fixed an error when creating a playblast with a USD camera in Maya in some cases
- fixed a bug that in some cases the media preview didn't show the correct exr channel when switching channels
- fixed a bug that in some cases the media preview didn't show the correct files when opened from the State Manager
- fixed an error when querying the feedback status from older Kitsu versions
- removed the scaling of.fbx files on import/export in Blender

## Prism 2.0.0.beta17

- added new plugin: Studio, which includes features to manage teams across multiple projects like:
	- assigning users to projects
		- marking projects as active or inactive
		- manage roles and permissions for users
		- apply Prism User Settings overrides studio wide
- added "Recent" menu to the Project Browser to open recent scenefiles
- added option to launch DCCs from the Project Browser using environments defined in the Prism Launcher
- added new login window which allows to login using a webbrowser
- added support for Unreal 5.2
- added support for Arnold in Maya 2024
- added option to save playblasts from Maya, 3dsMax and Blender to custom render locations
- added option to communicate between Prism instances in different DCCs using sockets
- added option to create stitched USD filesequences from the Prism Filecache LOP
- added option to create empty Usd files in the Libraries tab
- added option to open the Usd Editor for Usd files in the Libraries tab
- added option to change the product in the USD Export state in Houdini when connected to nodes other than the Prism Filecache
- added option to select existing identifier in the Prism Render LOP in Houdini
- added option to add assets from Prism libraries to the Houdini Layout LOP
- added PRISM\_HOUDINI\_PLAYBLAST\_USE\_NEW\_VIEWPORT env var to force a new viewport to open for playblasts. The default depends on the playblast settings.
- added PRISM\_HOUDINI\_PLAYBLAST\_SHOW\_MPLAY to enable/disable mplay for Houdini playblasts. Default is on.
- added option to connect Houdini Export and ImageRender states to existing nodes from a list by rightclicking on the "Connect to selected ROP" button
- PolyHaven files get downloaded in multiple threads now, which speeds up the download a lot
- added option to set thumbnails for files in the Libraries tab
- added options to select if a usd file should be loaded as layer or reference (payload) in Maya
- added option to specify which usd prim to reference in Maya when loading a usd file
- added option to include object parents in Usd exports in Maya
- added option to override the resolution for exported images from Photoshop
- added option to sync media playlists between Kitsu and Prism
- added support for progress bar in Deadline USD renderjobs
- added support for submitting media conversion jobs as a dependent job of render jobs to Deadline
- added option to specify a startframe for media conversions
- added support for selecting multiple project widgets and remove or open them in the file explorer all at once
- added support for Shotgrid projects with episodes
- added multiple improvements for the connection between ZBrush and Prism
- combined the "User Settings" and "Project Settings" into one "Settings" window
- fixed an error when opening the Prism User Settings in some cases, when the option to open Houdini scenes in manual update mode is enabled
- fixed a bug that the framerange of an export state in Houdini couldn't be set in the State Manager if the state was connected to a Prism Filecache SOP
- fixed a bug that Deadline USD renders didn't use the rendersettings prim, which was set on the LOP node in Houdini
- fixed a problem that Karma couldn't be used in Prism standalone
- fixed several bugs when dragging files in Prism when the project folder is on an unmapped network path
- fixed an error when creating a standalone USD playblast in some cases
- fixed a bug that the "Media Conversion" setting was not applied to new states when it was set in the state default settings
- fixed a bug that Houdini single frame playblasts couldn't be saved as mp4 videos
- fixed a problem that Houdini playblasts couldn't be saved as mp4 videos in some cases when the viewport resolution had odd numbers
- fixed a bug that media conversions of playblasts didn't work in some DCCs
- fixed an error when trying to export a USD file using the USD Export SOP in Houdini
- fixed an error when importing an FBX file from a custom location into Houdini
- fixed an error when applying default settings to a state in some cases
- fixed a bug, that the first frame in Maya playblasts was not updated correctly in some cases
- fixed a bug that the "sceneSaved" callback wasn't triggered in Nuke
- fixed a bug that caused Deadline nuke jobs to error

## Prism 2.0.0.beta16.3

- added option to drag and drop asset products from the Libraries tab into the DCCs
- added option to write out usd file sequences from the Prism Houdini Filecache LOP
- added support for the Karma Deep renderproduct in Houdini
- added option to submit attachments from Open RV to Kitsu
- added a first experimental version of a Prism Read node in Nuke
- added option to update Houdini scenes in manual update mode (in the user settings or by pressing alt while opening a scene)
- added env var PRISM\_USE\_ARNOLD\_USD\_EXPORT\_CONFIG to use the Arnold configuration for Maya USD exports
- added various improvements to the Unreal plugin when importing and exporting shots
- fixed an error when playing back the last frame of an image sequence in the Media Browser in some projects
- fixed a bug that PolyHaven USD assets couldn't get downloaded inside of many DCCs
- fixed a bug that the file format filter for libraries could be empty in new projects in some cases
- fixed an error when importing an alembic file in Houdini when the productname contained characters, which are not allowed in Houdini node names
- fixed some bugs and problems with the error reporting of the Prism Filecache and Render LOP when executed on Deadline
- additional minor improvements and fixes

## Prism 2.0.0.beta16.2

- added option to assign materials to USD prims in the USD Layer Manager using drag&drop
- fixed a bug that some framerange options on the Prism LOPs filecache node and the Prism LOPs render node were not working
- fixed a bug that media files were not displayed in the Project Browser in some cases
- fixed an error when the shot framerange in Kitsu was invalid in some cases
- fixed a bug that Unreal renders didn't use existing render settings
- fixed a bug that only a single file of a filesequence in Houdini was exported or rendered if relative paths were enabled
- fixed a bug that master versions were loaded in different places in Prism even if master versions were disabled in the project settings
- fixed some other minor bugs

## Prism 2.0.0.beta16.1

- added a new plugin: Cloud (alpha)
- fixed a problem that some plugin didn't work in Python 3.10 (and therefore in newer Blender releases)
- fixed a bug that the Prism plugin in some RV versions wasn't loaded
- fixed an error when publishing media from the versions list in the media browser
- fixed an error when closing the render window in Resolve in some cases
- fixed an error when importing shots into Unreal in some cases
- fixed an error in Unreal when trying to create a USD layer when the Unreal USD plugin is not loaded
- fixed a bug that USD layers were ordered incorrectly in some cases
- fixed an error when reordering relative USD layers in some cases
- fixed a bug that "new version available" popups were shown for master versions, when master versions were disabled in the project settings
- fixed a bug that the framerange of Houdini LOPs export states could only be changed on the nodes
- fixed a bug that the edit shot window was opened when selecting a custom output entity on Prism Solaris nodes
- fixed a bug that relative paths in the Solaris import HDA were changed to absolute paths in some cases

## Prism 2.0.0.beta16

- added new plugin for open source media player [Open RV](https://prism-pipeline.com/docs/latest/plugins/Open%20RV/#plugin-openrv)
- added option to set user and project environment variables persistently
- added option to make OCIO env var persistent (useful for apps, which require OCIO to be set before Prism is loaded)
- import nodes at the /obj level in Houdini have now the entity name of the imported cache in their nodename
- fixed an error when reparenting relative layers in the USD Layer Manager
- fixed a bug that the OCIO settings in Houdini were not refreshed, when setting whe OCIO in the "Media" tab of the project settings
- fixed a problem that paths starting with double backslashes in environment variables in Houdini were changed to single backslashes (fixes loading an ocio config from the network)
- fixed an error in the installer
- fixed an error when publishing media to Kitsu/Shotgrid/FTrack
- fixed an error when switching GPU Open libraries before all thumbnails are loaded
- fixed a problem that notes were not displayed in the "Review" tab in the Project Browser
- fixed an error when adding shot media to a playlist
- fixed an error when creating a reply to a note with the Prism Project Management enabled
- fixed an error when opening the USD Layer Manager in Maya
- fixed additional errors and bugs

## Prism 2.0.0.beta15

- added "Review" tab to the Project Browser to manage and view media playlists (part of the Project Management plugin)
- added auto generated thumbnails for exr and videofiles to improve performance
- added option to disable the media preview
- added option to create multiple assets, folders sequences and shots at once by separating entity names with ";"
- added environment variable PRISM\_LAUNCHER\_CONFIG, which can be used to display different DCC versions for different projects
- added AMD GPU Open library to download MaterialX materials
- added support for exporting animations using Multiverse in Maya
- added option to open media version in Windows explorer by ctrl + double clicking the version item
- added option to set the name of the external media player in the Prism User Settings
- added option to the Media Converter to use the Project FPS for video outputs
- added options for camera and resolution overrides to the Prism Render LOP node in Houdini
- added option to the Prism LOPs Filecache node to flush the cache after each frame
- added option to cache out a Solaris usd locally and submit only the husk render job to Deadline
- added option to export USD layers from USD Stage Actors in Unreal
- added option to export USD files in Unreal as department or sublayer into Prism entities
- added support to run Prism with PySide6 and PyQt
- Houdini usd\_export jobs before a husk job will now export in a single task in order to write all frames in a single usd file
- updated RPR Hydra delegate to v2.3.19
- fixed an error in Deadline render jobs submitted from Solaris
- fixed a bug that prims above a layer break were not rendered when caching the stage to disk before rendering or when submitting a husk job to the farm
- fixed an error when changing the renderer in the Standalone USD render state
- fixed a bug that the USD Layer Manager couldn't open files or add layers from the Product Browser window
- fixed several problem with the layer reordering in the USD Layer Manager
- fixed a problem that media conversions weren't working in some cases when no OCIO was set
- fixed a bug that Blender didn't prompt to save before opening a new scenefile
- fixed an error when importing images into Photoshop
- fixed a bug that files could be displayed in the Media identifiers list
- fixed a bug that Maya shelf files were not loaded from the Prism project folder
- fixed many more errors and bugs

## Prism 2.0.0.beta14.1

- added option to set the status for new Kitsu notes
- added option in Unreal to select FBX import type (static mesh, skeleton mesh or animation)
- added support for creating Arnold Materials when dropping textures in the Houdini nodegraph
- the status for published Kitsu product and media versions is now defined by the status of the Kitsu revision and not by the status of the task/comment
- the status of Kitsu notes is now visible on the note widgets in Prism
- updated the supported Arnold version in the USD viewport to v7.1.4.2
- fixed a bug that Kitsu comments were not displayed in Prism in some cases
- fixed a bug that on some computers the Poly Haven thumbnails couldn't be downloaded
- fixed an error when switching categories in the Poly Haven library in some cases
- fixed a bug that Poly Haven assets couldn't be downloaded as USD files, because the gltf -> USD conversion failed
- fixed an error when rightclicking a Poly Haven widget, which wasn't downloaded yet, when the Media Extension plugin was loaded
- fixed a bug that some Poly Haven items were not displayed correctly when more than 20 items were visible at once
- fixed an error when thumbnail images couldn't be saved because of missing permissions to create the parent folder
- fixed an error when changing the output color space in the Media Converter using the arrow keys
- fixed an error when adding an Burn-In modifier in the Media Converter in the advanced mode
- fixed an error when rightclicking the empty media preview in the Project Browser when the project was connected to a project management tool
- fixed a bug that OCIO were enabled for all Houdini playblasts
- fixed an error when opening a stage in the USD Layer Manager
- fixed an error when opening the Prism tray from the Prism User Settings
- fixed a bug that the export states in Maya created new selection sets when opening the State Manager for the first time in a session
- fixed a bug in Unreal that some old assets got selected after importing files through the Content Browser
- fixed an error when opening the library tab after a Substance Painter export

## Prism 2.0.0.beta14

- added plugin for [Unreal Engine Prism integration](https://prism-pipeline.com/docs/latest/plugins/Unreal%20Engine/#plugin-unrealengine)
- added Poly Haven library to the Project Browser to easily download HDRIs, asset models and textures
- added support for displaying different channels of multichannel exr files in the Media Browser
- added support for OCIO view transforms when selecting an output color space in media thumbnails or the media converter
- added option to set the required length of the publish comment
- added option for locking scenefiles to prevent that multiple artists open the same scenefile
- added support for video input files in the Media Converter
- added option to cancel media conversions
- added option to change the Prism standalone stylesheet
- added option to use @project\_name@ in export and render location names and paths in project presets, which will get replaced with the actual projectname during project creation
- added option to specify machine limit for Deadline jobs
- added option to the LOP Render HDA to cache out the USD stage in Solaris before rendering
- added option to submit USD renders from Solaris to Deadline as cache + python/husk render jobs, to remove the requirement for a Houdini license during rendering
- added support for rendering deep exr images using Mantra
- added support for submitting and rendering Mantra ifd files on Deadline
- added support for reading frameranges from filepaths which have a cryptomatte AOV name after the framenumber
- added option to the LOP filecache node to "Track Primitive Existence to Set Visibility" and enabled it by default
- added a "previous filepath" knob to the WritePrism node in Nuke
- added a custom drop handling for files in the Nuke nodegraph, which detects file sequences
- added option to use relative paths in Nuke
- added option to specify PRISM\_LICENSE\_FILE environment variable, which points to a json file, which can contain access keys so that no manual login is required when setting up new workstations
- improved playblast speed in Houdini by hiding the original viewport when the playblast is captured in a cloned floating panel
- when connecting render nodes in Houdini to a state, the framerange and format from the node will be applied to the state settings
- when creating an export state in Maya a unique product and set name will be set by default
- locations in the project settings can be edited by double clicking now
- improved connection details when the Hub cannot query server information
- the "Use Relative Paths" parameter on the ROP node in the LOP Filecache node is now linked to the relative paths setting in the USD Prism Project Settings
- render settings in Resolve are now remembered when reopening the render window
- renamed "Textures" tab to "Libraries"
- fixed a bug that caused that Prism standalone couldn't be launched from a network drive
- fixed a bug that the media converter froze after writing a few frames to a video file
- fixed a bug that some exr images couldn't be converted
- fixed a bug that the media converter didn't accept files with some specific naming as input
- fixed a bug that variables in the overlay in the Media Converter were evaluated only for 3d renders
- fixed a bug that shotscenefiles without a versioninfo.json file were not displayed in the Project Browser with the information, which could be extracted from the filename
- fixed an error when saving a layer in the USD layer manager in some cases
- fixed an error when creating a "Save HDA" state in Houdini
- fixed a bug that exported Houdini shotcams didn't inherit the transform from their input nodes
- fixed a bug that playblasts in Houdini didn't use the same OCIO display as in the viewport if it was different than the default display
- fixed a bug that the filecache SOP in Houdini couldn't read negative frames
- fixed a bug that Deadline jobs submitted from Solaris didn't have the identifier in the jobname
- fixed a bug that renders with Arnold in Houdini could only write exr files
- fixed a bug that mayapy crashed when the userSetup.py was loaded twice without creating a QApplication first
- fixed an error when submitting 3ds Max jobs to Deadline
- fixed a bug that the import images option in Nuke didn't work when there was a space in the image filepath
- fixed a bug that hidden Shotgrid status were synced to Prism
- fixed a bug that publishing mp4 videos to Kitsu uploaded only the first frame
- fixed a bug that Kitsu departments weren't synced to Prism when no task types were defined in the Kitsu project
- fixed an error when connecting a tvshow Kitsu project without episodes to Prism

## Prism 2.0.0.beta13

- added new MediaExtension plugin, which includes a powerful media converter with OCIO v2 and text overlay features
- added option to customize Deadline jobnames in the project settings
- added viewer control to the media preview in the Project Browser for play, first, previous, next and last frames
- added a new dropdown to select a media source when multiple media files from different sequences are in the same folder
- added option to submit playblasts from Maya to Deadline
- added option to submit exports from Maya to Deadline
- added option to set the Subdivision Method for USD exports in Maya
- added option to select and import multiple assets and shots at once into Solaris and connect them to the LOP Sequencer node
- added option to save current states in the State Manager as a new preset
- added option to disable the remembering the active tab in the Project Browser
- added option to set the version, comment and rename the files when drag&drop files into the scenefiles tab in the Project Browser
- added option to open textures from Substance Painter in the Texture Library after exporting them
- added option to the LOP Render HDA to use the framerange of the output context shot
- added option to export FBX files with a specific framerange from Maya by deleting keyframes outside that range
- added option to save Maya playblasts as mp4 videos with audio
- added "project\_name" to the available key in the project template paths
- added support for environment variable PRISM\_DEADLINE\_PYTHON\_VERSION to override the python version for python Deadline jobs
- added support for env var PRISM\_MAYA\_SET\_VISIBLE\_OBJECT\_TYPES to control if Prism sets the visible object types for Maya playblasts
- the playblast resolution in Houdini without a resolution override is now taken from the camera settings instead of the current viewport settings
- USD files will be imported into Solaris now when importing them using the Project Browser
- Maya USD export will now export only the selected objects and not all the parents as well
- image planes are now visible in Maya viewports when using the "recommended settings"
- the thumbnail videos generated by the ProjectManagement plugin are now using the filename from the source media files
- pressing the refresh button in the Project Browser will now clear the query cache of the Shotgrid, Kitsu and FTrack plugin
- the Project Management setup window is now prefilled with the url and user credentials if they were previously entered
- the jpg quality for Photoshop exports is now using a value of 10 by default
- fixed some crashes related to the media preview in the Project Browser
- fixed a bug that the "Copy path for next version" option was not available when rightclicking in an empty area of the product version list
- fixed a bug that drag&drop of files didn't work in some cases when the files were on a Windows network drive
- fixed a problem that in some cases the wrong version number of master product and media versions were displayed
- fixed a bug that the publish comment in the State Manager was not used in some cases for the generated product and media versions
- fixed a bug that the deprecated app version sanity check popup could show up in older projects
- fixed a bug that an import option was shown in the Product Browser in Prism Standalone
- fixed a bug that not all files of a ShotCam productversion got renamed correctly when setting it as the master version
- fixed a bug that shotcams couldn't be exported from asset scenefiles
- fixed an error when renaming shots
- fixed an error when opening manually saved scenefiles in some cases
- fixed a bug that updating multiple import states at once caused the same file to be imported in every selected import state
- fixed an error when loading some state types in 3ds Max
- fixed an error when using the "Connect selected reference node" button in Maya on an import state
- fixed a bug that the postExport callback was not triggered when textures were exported with warnings in Substance Painter
- fixed a problem that Prism could cause a "...didn't shut down correctly" waring in Substance Painter
- fixed a bug that it was not possible to export textures in Substance Painter to custom export locations
- fixed a bug that the renderjob Submit UI in Nuke was broken, when changing the framerange type
- fixed an error when opening the State Manager in some cases when the Deadline pool presets are enabled in the project settings, but don't contain a valid preset
- fixed a bug that the active Prism project got changed by Deadline jobs running in the background
- fixed a problem that caused that Prism wasn't loaded in Nuke Indie
- fixed an error when opening the Project Browser after installing the USD plugin without restarting Prism
- fixed an error when importing usd files into a Maya shotscene if the usd file has an invalid defaultPrim defined
- fixed some problems with updating USD layers in the USD container when using relative paths in some cases
- fixed an error when saving the root usd layer in the Layer Manager from the context menu under a custom name or under a product
- fixed an error when saving a layer in the Prism USD Layer Manager on a Windows network drive in some cases
- fixed a bug that the Turntable preset couldn't be loaded into the Prism USD Layer Manager
- fixed an error when syncing product and media status from Shotgrid
- fixed a bug that FTrack assets were not displayed in Prism if it was nested inside multiple folders
- fixed an error when executing the Prism Filecache node in Houdini in background
- fixed a bug that the "Save to Disk" button submitted a job to Deadline if the "Submit Job" checkbox was checked on the export state of the Prism Filecache SOP in Houdini
- fixed a bug that high prio Deadline cleanup jobs could cause following Redshift export jobs to fail
- fixed some warning when opening Houdini from the Launcher in some cases
- fixed a bug that Houdini cameras in subnets couldn't be exported as Shotcams to an alembic file
- fixed an error when submitting a LOP rendernode to Deadline in some cases

## Prism 2.0.0.beta12

- added multiple new features to the USD Layer Manager tool like authoring of the scenegraph, variants, references and improved layer management
- added option to use relative paths in USD files
- added the option to export USD files from Maya as a USD container, a layer or as a custom product
- added a reload option to the context menu of the USD viewport in Prism
- added option to define default settings for every state type in the State Manager (in the "State" tab of the project settings)
- added option to use wildcards and Python expressions to define in which scenes state presets should be applied by default
- added option to copy product and media versions between locations
- added option to write Texture Library thumbnails to disk for faster thumbnail display
- added option to copy only the selected texture path of a Texture Stack widget in the Texture Library
- added option to set if the scenefile should be versioned up during a publish or not
- added option to use relative paths in Houdini (added to the project settings)
- added option to merge sets in Maya when renaming a productname of an export state if the name already exists in the scene
- added the option to view assigned tasks from other users in the Tasks tab in the Project Browser
- added "postExport" callback to the Substance Painter plugin
- added option to sync the task/version status list from Shotgrid
- added support for displaying image attachments in Shotgrid notes
- added option to use Asset<->Shot connections from Shotgrid
- added option to use the Shotgrid, FTrack or Kitsu usernames in Prism
- added the option to play media or open it in the media browser from the WritePrism node in Nuke
- added option to submit scenefiles with Deadline jobs (enabled by default)
- added option to restore default departments in the project settings
- updated Python in Prism standalone to v3.9
- updated USD to v22.08
- updated the supported Arnold version for the USD Hydra delegate to 7.1.3.2
- updated the AMD RPR Hydra delegate to v2.2.61
- the location dropdowns in the Project Browser now affect which products, identifier and versions are displayed
- creating a new USD departmentlayer in the Product Browser is creating now an empty USD file and adds it as a layer to the entity USD container
- automatically generated USD container and departmentlayer versions are created now in the same location as the exported file, which triggered the automatic generation
- USD imports in Blender are importing USD preview materials now
- assigned tasks from omitted Shotgrid assets and shots are not displayed in the Tasks tab anymore
- tasks with the status "Omit" are now hidden by default in the "Tasks" tab
- in the RV and DJV path browse window it's possible now to select executables
- master product versions are now enabled for new projects by default
- master versions get updated now after Deadline jobs are finished
- improved warning and debugging messages if Prism couldn't get loaded in Maya
- improved validity checks for the Kitsu url during Project Management setup
- the "Mute Departments" option on the Prism Solaris Import HDA is now disabled by default, because it causes some Houdini display bugs
- fixed a bug that wrong versions were displayed in the "Execute as previous version" menu of LOP Render states
- fixed a bug that the render HDA in Solaris could show an "Invalid camera" in some cases although the stage is valid
- fixed a bug that the scale option on the Houdini LOP import node didn't scale cameras
- fixed a bug that Prism LOP Render nodes in Houdini needed to be cooked before publishing
- fixed a bug that some parameters on the Prism Filecache SOP node in Houdini were reset when copy/pasting the node
- fixed an error when rightclicking a Shotcam export state in Houdini
- fixed a bug that states in Houdini were not executed in some cases when they were triggered from HDAs, but they were disabled in the State Manager
- fixed a bug that Houdini network pane thumbnails were created in the wrong network pane if multiple network panes were open
- fixed an error when creating a "Save HDA" state in Houdini while no node is selected
- fixed an error when exporting an existing HDA to a new file in Houdini 19.5
- fixed an error when submitting python jobs to Deadline (for example when doing Redshift or 3Delight submissions)
- fixed an error when exporting USD files in Maya with some material types
- fixed an error when Prism tried to delete unknown, locked Maya nodes before an export
- fixed a bug that the username of product versions were incorrect in some cases
- fixed an error when creating a scenefile version from a preset in a subfolder
- fixed an error when exporting USD files to Windows network drives in some cases
- fixed an error when dropping invalid content into the Texture Library in some cases
- fixed a bug that double clicking an assigned Shotgrid tasks didn't select the correct asset, if the asset didn't have a category assigned in Shotgrid
- fixed an error when selecting entities in the Import Media window in Resolve
- fixed a bug that media identifiers in custom render locations were not displayed in the import window in Resolve
- fixed an error when opening the entity window in the PureRef export window
- removed the "Global Framerange" settings in the State Manager
- removed Hydra delegate for 3Delight (temporarily)
- many additional smaller improvements and fixes

## Prism 2.0.0.beta11.9

- added support for specifying any executable in the RV/DJV path settings in the user settings, which can be executables of other media players
- added option to the LOP Import node in Houdini to reverse the vertex ordering
- added options to the Filecache and Render LOP nodes in Houdini to use the framerange from the meta data of another node
- added scale option to the LOP import node in Houdini
- added a refresh button and a warning to the Prism Hub if there is no connection to the server
- added the filesize to the texture widgets info in the Texture Library if filesizes are enabled in the Project Browser
- improved the thumbnail quality for exr, hdr and dpx images in the Project Browser
- improved the Mute Departments HDA in Houdini so that it affects only the downstream nodes instead of the whole session
- automatically generated USD container and departmentlayer USD files have now a default prim defined, which fixes several problems
- Prism shows a warning now when Maya USD exports will include namespaces to avoid name conflicts
- fixed a bug when trying to open the Prism console from a location with a space in the path
- fixed a crash on Houdini startup if a video file in the "Media" tab was selected by default
- fixed a crash, when switching quickly between mp4 versions in the Media Browser
- fixed some bugs when having two products, which differentiate only in their case
- fixed an error when saving the User Settings when the USD plugin was installed during the same session in some cases
- fixed an error when selecting tasks in the "Tasks" tab of the Project Management plugin in the Project Browser
- fixed an error when executing folder states in Python 2.7
- fixed an error when connecting assets to shots in Python 2.7 sessions
- fixed an error when opening Houdini scenes if filecache SOP nodes had a specific combinations of parameters values
- fixed an error when using negative values in the "width" parameters on the LOP Import node in Houdini
- fixed an error when the project resolution is set and a lighting preset is loaded in Houdini
- fixed an error when using tags on unloaded reference nodes in Maya
- fixed an error when exporting images from Photoshop in some cases
- fixed a bug that the Project Management Setup window couldn't be used inside of Nuke
- fixed a bug that the product list in the read section of the Prism Filecache LOP in Houdini didn't show all productnames in some cases
- fixed a bug that some parameters on the LOP filecache and render node in Houdini were set back to their defaults when copy/pasting the node

## Prism 2.0.0.beta11.8

- fixed an error when creating an ImageRender state in some DCCs
- fixed an error when setting the render settings prim on the Prism LOP Render node in some cases
- fixed a problem in the installer when the autoload of the PrismInternals plugin was disabled in the user settings
- fixed an error when opening scenefiles from Prism standalone in some cases

## Prism 2.0.0.beta11.7

- fixed a bug that Prism couldn't be launched on some computers with a default system encoding of cp1257
- fixed an error when opening DCCs from Prism standalone in some cases
- fixed an error when creating a USD export state in Houdini
- fixed an incorrect warning message when importing asset USD files in Maya
- fixed a bug when setting a product version, which has multiple files, as a master version
- fixed an error when loading the PrismInternals plugin after Prism has launched in some cases
- fixed an error when pressing "Cancel" in the product tag window
- updated PySide2, which fixes some problems with network installations

## Prism 2.0.0.beta11.6

- added option to connect assets to shots
- added option to add tags to products
- added option to generate USD files for shots with connected assets
- added toolbar and shortcuts to the USD viewport in the Project Browser
- added first person navigation to the USD viewport in the Project Browser (hold right mouse button and navigate using WASD)
- added many new features and improvements to the Prism Solaris workflow (many new options in the import and render HDAs, USD export LOP/SOP are replaced by a new Filecache LOP)
- added the option to publish any supported Houdini nodes using a new option in the node rightclick menu
- added support for publishing the componentoutput LOP node in Houdini
- added support for publishing the vellumio::2.0 SOP node in Houdini
- added multiple updates to the USD Standalone render (RenderSettings option, MPlay option, logging, faster sequence rendering)
- added new modes of Deadline job dependencies for Houdini jobs
- added option to the Houdini playblast state to save the playblast in custom locations
- added option to the Houdini playblast state to set the generated playblast as the new master version
- added option to not export UVs to USD files in Maya
- added support for using Prism in Resolve with Python 3.7, 3.9 and 3.10
- added Master Version Manager, a tool to check and update master versions in the project
- added the option to drag multiple files and subfolders into the products tab. A preferred file can be selected from the context menu. (Useful when ingesting USD assets, which consist out of multiple files)
- added media comments to the version list in the Media tab
- added option "Go to source scene" to the context options of product and media versions in the Project Browser
- added media notes of the Project Management plugin to the media tab in the Project Browser
- multiple performance improvements, especially in the Project Browser and startup times
- improved loading of thumbnails in the Texture Library, which now allows to open folders with hundreds of textures
- the media preview in the Project Browser is now resizable
- Deadline pools and groups are now stored in the project config instead of querying them on every Prism startup
- textures with colorspaces in their filenames are now grouped correctly in the Texture Library
- the displayed Prism version in the Launcher widget updates now to the current Prism version
- assigned Shotgrid tasks are now sorted by due date
- disabled the relative path output processor on the USD ROP in Houdini in the filecache node, because this caused problems with texture paths
- fixed a bug that applications launched from Prism standalone could behave differently as when launched manually (e.g. plugins not loaded)
- fixed an error when browsing for a project image when no current project is active
- fixed a problem that master versions couldn't get overwritten in some cases if they were used by other processes
- fixed a bug that product versions couldn't be drag&dropped in some external applications
- fixed a bug that doubleclicking a product item in the Product Browser didn't recognize the master version as the latest version to import in some cases
- fixed several bugs related to master product and media versions
- fixed a bug that the "Copy path for next version" didn't work for playblasts and 2d renders
- fixed a bug that could cause slow performance in Houdini when using many export states in big scenes
- fixed some bugs that Prism HDAs in Houdini Solaris could trigger unwanted cooking of upstream nodes
- fixed some problems when using custom output contexts on the Prism filecache node in Houdini
- fixed a bug that Blender scenefiles and playblasts couldn't be saved on unmapped network drives
- fixed a bug that Maya scenes were not opened in some cases after pressing "Save" in the unsaved changes popup
- fixed a bug that Multiverse USD exports in Maya were not working
- fixed an error when importing USD objects using Multiverse multiple times
- fixed a bug that the transform node of Multiverse Compoundshapes didn't get deleted when deleting an import state
- fixed a problem that Prism couldn't be loaded in Photoshop on some computers
- fixed an error when submitting a Deadline priority job in some cases
- fixed an error when opening scenes in non gui sessions (like Deadline jobs) in some cases
- fixed a bug that the parent item of selected assets in the Project Browser weren't expanded in some cases
- fixed an error when opening the Dependency Viewer when a circular dependency existed on the product
- fixed an error when unloading the ProjectManagement plugin in some cases
- fixed an error when querying Shotgrid data in some cases
- removed the "Collect Versions" list in the media tab
- removed the "Copy Version" option from the context menu in the Scenefiles Browser, because it's functionality overlapped with the "Copy" option

## Prism 2.0.0.beta11.5

- added options to configure State Manager presets, which can be applied by default to specific entities/departments/tasks
- added option to states in the State Manager to play previously generated media in external media player
- added option to states in the State Manager to view previously generated products and media versions in the Project Browser
- added option to set required plugins in the project settings, which need to be loaded to open the project
- added support for Houdini wedging to the export state and Filecache node
- added the option to the Houdini Filecache node to export to different entities
- added the option to the Houdini Filecache node to fetch the framerange from parent Lop nodes
- added support for the vellumio node in the export state in Houdini
- added option to use texture master versions (can be enabled in the Project Settings)
- added option to filter specific fileformats in libraries
- added option to apply project resolution in the Render and Playblast states
- added option to import all outdated products with one click when opening a scenefile
- when opening Prism standalone while there is already a running Prism standalone process, the Project Browser of the already running process will open now
- when changing asset/shot selection in the Project Browser, the currently selected department, task, product and media identifier will be remembered
- sanity check messages aren't blocking the loading of scenefiles anymore
- improved MaterialX network creation in Houdini when dropping textures in the nodegraph
- USD departmentlayer don't need to match the department names in the Project Settings anymore
- the "complexity" (shortcut s) setting in the USD viewport can now be used to smooth alembic geometry
- when importing Shotcams into Houdini, the resolution parameter will be set to the resolution meta data saved in Shotcam products
- clicking on the "Export", "Render" or "Playblast" buttons in the State Manager shows now a list of all available states of that category
- the departments in the project settings are now synced from Kitsu if Kitsu is enabled for the current project
- improved compatibility with Prism 1 projects
- fixed a bug that media in custom locations couldn't be set as master
- fixed a bug that only one entity could be selected in the Project Browser
- fixed an error when setting the status of a task, product version or media version to a Kitsu status, which has upper case characters in it's short code
- fixed an error when starting Prism when the OCIO variable was set in the Prism user environment settings
- fixed an error when launching Prism after using the setup.bat
- fixed an error when launching apps from the Prism launcher, when no project is active
- fixed an error when setting the framerate in Blender
- fixed an error when importing USD files into Maya using Multiverse in some cases
- fixed a bug on the Nuke WritePrism node that some knob where displaying an error when some specific output formats where selected
- fixed a bug in Nuke that the WritePrism nodes didn't show the correct output filepath after a Nuke scene was loaded
- fixed a problem that alembic and usdc files couldn't be deleted after getting displayed in the USD viewport until Prism was closed. Now it's enough to close the USD viewport.
- fixed an error when creating a USD export SOP node in Houdini when the scenefile is saved in a department, which doesn't exist in the project settings
- fixed a bug that states in the State Manager could loose their connection to nodes in the scene in some cases
- fixed a bug that the Prism Filecache node in Houdini wasn't loaded when opening a scene in some cases
- fixed a bug that empty product versions could be chosen as the latest version to load in Prism Filecache nodes in Houdini
- removed option to use symlinks for master versions

## Prism 2.0.0.beta11.4

- added support for DCCs which are using Python 3.10 like Blender 3.1/3.2
- added support for the latest Substance Painter version, which uses Python 3.9
- added options to switch the shading mode in the USD viewport in the Product tab (from context menu or using "w")
- added option to set the visibility explicitly on prims in the LOP import node
- added option to create MaterialX materials when dropping textures into the Houdini nodegraph
- added option to open scenefiles from the Texture Library
- added option to set a scenfile thumbnail as entity thumbnail
- added option to use the filename instead of the full filepath in Kitsu comments when publishing products or media to Kitsu
- added commandline arguments to the installer executable, which allows to install Prism without GUI
- the "Create emtpy USD file" option is now available for all product names
- Prism metadata in USD stages is now saved on a special primitive instead of the stage metadata to allow easier authoring
- improved the readability of Kitsu publishes by adding more linebreaks
- the default state name of custom imports in the State Manager is now the imported filename
- Maya fbx exports will now include all children of the objects, which are added to the object list of an export state
- fixed a bug that the Prism Filecache node in Houdini couldn't load any geometry when submitted to Deadline
- fixed an error when showing the autosave popup in some cases
- fixed an error when the app plugin couldn't be loaded and added a warning message instead
- fixed a bug that the uninstaller window couldn't be launched
- fixed an error when setting a project thumbnail by broswing to a file
- fixed an error when opening the Launcher when the active project didn't have a project thumbnail
- fixed an error when saving the Project Settings when the project doesn't have a thumbnail
- fixed a bug that products and media were saved with wrong version numbers in some cases if master versions and multiple locations were used
- fixed an error when drag&drop a file into the TextureLibrary
- fixed a bug that the rstexbin conversion option was available for rstexbin files
- fixed a bug in Resolve that shots could be imported only one by one
- fixed an error when displaying the state settings of the dependency state in Houdini in some cases
- fixed an error when refreshing assigned Shotgrid tasks, when tasks are assigned to no assets or shots
- fixed an error when trying to connect to a Shotgrid site, which doesn't exist
- fixed a bug that the "Camera" setting in the ImageRender state was not applied to Renderman in Maya
- fixed an error when the Maya workspace couldn't be set because of missing permissions
- fixed an error when importing Maya asset scenefiles into other Maya scenes using the State Manager

## Prism 2.0.0.beta11.3

- fixed a bug that the "Create Entity" and "Edit shot settings" were not visible when rightclicking an asset/shot
- fixed an error when opening the Texture Library if the Project Settings haven't been saved with beta11.2+
- fixed a bug that the scenefile list were not refreshed after a file was drag&dropped into the scenefile list

## Prism 2.0.0.beta11.2

- added option to add custom library locations to the Texture Library tab in the Project Browser
- added the option to open and copy multiple files from the texture library at once
- added the option to convert textures in the Texture Library to.rstexbin (can be enabled in the project settings)
- added thumbnails for videofiles in the texture library
- added options to create Deadline pool presets, which define Pool, Secondary Pool and Group for a Deadline job (in the project settings)
- added option to show filesizes for scenefiles, products and media (in the Project Browser options)
- added support for previewing.tga files
- added option to convert media to prores 4444
- the "copy path" option was changed to "copy" in most places in Prism, which copies the file itself additionally to the filepath
- added Prism menu to Maya menubar
- added object tagging to Maya, which allows to predefine objects for export states
- added new "Prism LOP Sequencer" HDA to Houdini, which allows to playback shotinputs in sequence
- added options to the LOPs import node to reload, add layerbreak and mute downstream departments
- added the option to specify which Prim to load when using payloads in the Prism LOP import node
- added options to the LOP render, LOP export and SOP USD export node to specify to which asset/shot and department the files should be written to
- the Hydra delegate in Houdini will now be switched to GL during saving and publishing to improve stability
- the setup.bat in the Prism install folder can now be executed without admin permissions
- setting a framerange to "custom" uses now the current scene range as default in all DCCs
- ZBrush export settings are now remembered during the session
- backslashes in the assetpath on LOP import nodes are now converted to forward slashes
- fixed a bug that Redshift AOVs couldn't be saved as a multilayer exr in Houdini
- fixed a bug that executing multiple Redshift states in Houdini did not work correctly in some cases
- fixed a bug that some state settings were not visible after using the "Submit Job..." button on Prism HDAs in Houdini
- fixed a bug that the browse button for the Hython executable in the User Settings was not working
- fixed a bug that it was not possible to set the FPS in Maya to float numbers like 29.97
- fixed an error when trying to change the product name to an invalid name in an Export State in Maya
- fixed a bug that additional export locations were not displayed in the Product Browser
- fixed a bug that media in additional render locations were not displayed and versioned correctly in the Media Browser
- files with "cryptomatte" in their name are sorted after other files now in the media preview in the Project Browser
- fixed an error when editing the comment of a media version, which doesn't contain media files
- fixed a bug that ingested 2d and playblast media created a versioninfo file at the wrong location
- fixed a bug that 2d media couldn't be set a master
- fixed an error when ingesting playblast sequences in the Media Browser
- fixed an error when pressing enter in the "Create Task" window
- fixed an error when Prism didn't have write permissions for the internals.prism file
- fixed an error when cancelling the automatic thumbnail generation in Nuke
- fixed a bug that the selected asset in the Texture Library were not carried over to other tabs
- fixed a bug that files in the sequence folder could be displayed as shots in the Project Browser
- fixed a bug that the preview paths in the "Folder Structure" tab of the Project Settings were not resolved with the entered template before saving
- fixed a bug that state settings were not displayed after a state was created in the State Manager in some cases
- fixed a bug that the Product Browser was not showing the correct version on startup when opening it from an import state in some cases
- fixed an error when creating a WritePrism node in Nuke in some cases
- fixed an error in the ProjectManagement plugin when a product master version had no valid files
- fixed an error when refreshing assigned Kitsu tasks when Prism is run with Python 2
- fixed a bug that unnecessary information was printed into the Houdini console when using the Kitsu plugin
- fixed an error in the Kitsu plugin when Kitsu tasks didn't have a department assigned
- fixed an error when having shots in FTrack, which don't have a sequence
- fixed a bug that the stylesheet in Prism standalone was broken when the Prism installation folderpath contained special characters
- fixed an error in the installer after the files got extracted in some cases

## Prism 2.0.0.beta11.1

- added options to create 2d and playblast media identifiers from the rightclick menu in the Project Browser
- added new State Manager state "Code" to execute custom python code and save/load code snippets
- added option to submit an additional "high priority job" to Deadline, which can render specific frames at a different priority than the main Deadline job
- added the option to specify a secondary pool for Deadline submissions
- added warning when dropping media into the media preview of an existing version with the option to create a new version instead
- added options to the scenefiles rightclick menu to choose in which location a filepath should be opened/copied
- added support for opening the Prism tray multiple times on the same computer for different users
- added substeps to the Prism Filecache node in Houdini
- added support for submitting the Prism Filecache node in Houdini to Deadline using the State Manager or using a new submit button on the node
- added Multiverse export options, when exporting USD files using Multiverse in Maya
- added support for USD Material export in Maya using the Maya USD plugin v0.14.0 and above
- added asset thumbnails to the treewidget in the TextureLibrary
- added the option to create folders in the icon view in the Texture Library
- added an "Open Project Browser" button the the warning popup when a scenefile is not saved in the Project Browser
- added option to the Project Browser to open a Prism Console when in debugMode is enabled
- added.bat files to the "Tools" folder to launch Prism with a console for easier debugging
- added the option in the the USD viewport to display geometry with subdivisions when pressing "s" or by choosing a complexity from the context menu
- added option to the User Settings to show/hide the USD viewport by default
- added Kitsu episode names as prefix to the sequence name in Prism
- added priority indicators for assigned Kitsu tasks
- added support for having multiple levels of folders for FTrack assets
- added a warning popup that the FTrack plugin requires Python 3 if used in Python 2
- enabled the alembic hierarchy building from the "path" attribute in the Prism Filecache node
- task/version status icons are keeping their color now selected
- expanding and collapsing folders in the Project Browser happens now with one click on the item
- changed the "reference" option on the Prism LOP node to "payload"
- importing asset USD products into Maya will create payloads now instead of references
- deleting import nodes in the /obj level in Houdini, which were created using Prism will delete their import state as well now
- Kitsu task and version statuses are now queried directly from Kitsu and don't have to be configured in the project settings
- Kitsu task and version statuses, which are not allowed for the current user are hidden now from the "set status" menu
- changed the order of assigned tasks in the "Tasks" tab to match the order in Kitsu (by priority and name)
- paths defined in the PRISM\_PLUGIN\_PATHS and PRISM\_PLUGIN\_SEARCH\_PATHS environment variables are now displayed in the "Manage Plugin Paths" window
- updated ffmpeg to latest version (2022-04-03-git-1291568c98)
- fixed a problem that mp4 files couldn't be deleted while Prism was running, after Prism previewed the mp4 file
- fixed a bug that shot frameranges were displayed incorrectly when they started or ended at frame 0
- fixed a bug that the shot department selection got reset when switching tabs in the Project Browser
- fixed an error when changing settings on multiple states in the State Manager at once
- fixed a bug that master product versions were not created correctly in some cases
- fixed a bug that master versions were not automatically selected when opening the Product Browser from an import state
- fixed a bug that dragging over productnames in the "Products" list in the Project Browser didn't refresh the versions correctly
- fixed a bug that Houdini LOPs Deadline renderjobs were always submitted as Houdini 18
- fixed a bug that Nuke Deadline jobs had their outputpath set in the 3drenders folder instead of the 2drenders folder
- fixed a bug that could cause slowdowns in some Nuke versions
- fixed a bug that the automatic preview in Nuke was not working when the "srgb" colorspace was not available in the current scenefile
- fixed an error when importing USD files in Maya 2023 in some cases
- fixed an error when loading the USD plugin in Blender 2.83
- fixed a bug that Blender 2.83 could crash when opening a scenefile
- fixed an error when exporting geometry from ZBrush in some cases
- fixed a bug that when publishing multiple render states in Houdini using Mantra, only the first state was executed
- fixed an error when using the "Mute Departments" LOP node in Houdini when the current scene is saved in an invalid department
- fixed a bug that the Houdini filecache nodes didn't load correctly when the hipfile was opened by double clicking it in the standalone Project Browser
- fixed an error when unloading the Kitsu, Shotgrid or FTrack plugin when the ProjectManagement plugin wasn't loaded
- fixed a bug that departments and tasks could show up twice in the Project Browser when the ProjectManagement plugin was used with "Allow local tasks" enabled
- fixed a bug that instead of the "Edit Shot" dialog the "Create Shot" dialog opened when the ProjectManagement plugin was used
- fixed a bug that some popup messages from the ProjectManagement plugin stayed open after they should have been closed
- fixed a bug that setting a task status from the "Tasks" tab didn't display the new status in Prism until the cache was cleared
- fixed a bug that it was possible to create assets/shots/departments/tasks after the ProjectManagement setup was completed
- fixed an error when creating a USD export state in Maya when no USD plugin is loaded
- fixed a bug that assigned Kitsu tasks could appear multiple times in the Tasks tab
- fixed a bug that Kitsu urls didn't open correctly when the url in the project settings ended with "/"
- fixed an error when refreshing the Tasks tab and Kitsu asset tasks are assigned to the current user
- fixed a bug that Prism displayed the Kitsu "Task-Type" as department name instead of the actual Kitsu department name
- fixed a bug in Blender and Houdini when setting shotframerange when opening a scene when the Kitsu integration was enabled for the current project
- fixed an error in the Shotgrid plugin when assigned tasks didn't have a start and end date
- fixed an error when refreshing the "Tasks" tab when having FTrack asset tasks assigned
- fixed a bug that the "always on top" option in the Texture Library wasn't working
- fixed some crashes caused by the Texture Library
- fixed an error when clicking in an empty area in the notes section in the "Tasks" tab when a note is selected
- removed deprecated plugin types "ProjectManager" and "RenderfarmManager"

## Prism 2.0.0.beta11

- added new "ProjectManagement" plugin to assign tasks to users and add notes to tasks and versions, see [ProjectManagement Plugin](https://prism-pipeline.com/docs/latest/plugins/Project%20Management/#plugin-projectmanagement)
- added new "Shotgrid" plugin to connect Prism to Shotgrid, see [Shotgrid Plugin](https://prism-pipeline.com/docs/latest/plugins/Shotgrid/#plugin-shotgrid)
- added new "FTrack" plugin to connect Prism to FTrack, see [FTrack Plugin](https://prism-pipeline.com/docs/latest/plugins/FTrack/#plugin-ftrack)
- added new "Kitsu" plugin to connect Prism to Kitsu, see [Kitsu Plugin](https://prism-pipeline.com/docs/latest/plugins/Kitsu/#plugin-kitsu)
- added support for selecting multiple states in the State Manager at the same time and performing actions to all of them at once like changing settings, copy/paste and delete
- added option to edit the comment of product versions
- added the option to edit the comment of media versions and view the comment above the media thumbnail
- added a splashscreen when opening Prism standalone and specific apps
- added a Prism Deadline submitter to Nuke
- added support for rendering WritePrism Nuke nodes on Deadline
- added automatic thumbnail generation when saving a new version of a Nuke script
- added option to choose a previous version to render in Nuke
- added option to export USD files with materials in Maya
- added support for renderman in Maya
- added support for deep exr output with 3Delight in Houdini
- added option to select job Pools for Deadline submissions in the State Manager
- added option to drag&drop files into the item layout of the scenefile versions in the Project Browser
- added a new setup window to simplify the Prism setup without the installer executable (setup.bat)
- added a warning popup when loading a ZBrush file from Prism standalone
- added options to change the plugin install folder to the Hub and the installer
- added the option to use the environment variable "PRISM\_DATE\_FORMAT" to configure the date format in the Prism UI
- added possibility to stop publishing, saving and state executions from callback functions
- the USD viewport in the Project Browser frames now all geometry every time a product version is select. This can be disabled using the "Remember camera position" option in the context menu
- the previews in the Texture Library are loaded in multiple threads now to improve performance
- the windows username will be used as the default username after the first installation of Prism
- Deadline jobs, which were submitted from apps launched with the Prism Launcher will now render with the environment variables defined in the Launcher app
- changed the default plugin install folder to C:/ProgramData/Prism2
- changed the showOrnaments setting for Maya playblasts to "True" by default, but it can be disabled using the "PRISM\_MAYA\_SHOW\_ORNAMENTS" environment variable
- improved drag&drop handling of files into the texture library
- Blender and Substance Painter autosave files are now hidden in the Project Browser scenefile list
- files with the extension.db are now ignored in the scenefile lists
- capped the amount of frames in the hoverwindow of frame expressions to 1000 and the internal amount of frames generated by a frame expression to 10000 to avoid accidential freezes when typing too high numbers
- fixed an error when adding "x0" in a frame expression in the State Manager
- fixed a bug that the username were not updated when a scenefile was versioned up by a different user
- fixed a bug that 3Delight NSI rendering on Deadline created errors when using the <aov> variable in the filepath
- fixed a bug that the Deadline cleanup job failed when rendering Redshift or 3Delight scenes, which had spaces in their filepaths
- fixed a bug that Deadline tasks, which were dependent on other jobs were not released in some cases
- fixed a bug that it was not possible to render image sequences with Prism and VRay in Houdini
- fixed an error when pasting a project preview image from the clipboard
- fixed an error when refreshing the identifier list in the Products tab when the USD plugin was loaded
- fixed a bug when saving files in shots when the local project folder is enabled
- fixed a bug that the "Source Scene" was not listed in the dependency viewer for product and media versions
- fixed a bug that the versioninfo and dependency viewer was not available from the context menu of the media version list
- fixed a bug when capturing the automatic viewport thumbnail in Houdini when no viewport was visible in the Houdini UI
- fixed an error when drag&drop the current media preview in the Project Browser onto itself
- fixed an error when opening the "Create Shots" window in Resolve when offline media existed in the timeline

## Prism 2.0.0.beta10

- added new plugin "Launcher" to launch different versions of DCCs and manage environment variables
- added a new option to automatically save a viewport preview with all scenefiles saved in Houdini, Blender and Maya
- added option to show asset and shot thumbnails in the Project Browser lists
- added option to change the description of scenefiles in the Project Browser
- added options to create media versions and AOVs from the Project Browser
- added the option to ingest media files by dragging files into the media preview in the Project Browser
- added "Refresh" option to the context menu of all lists in the Project Browser
- added local/global indicator for scenefiles in the thumbnail view
- added options to import and export Prism User Settings
- added options to import and export Prism project settings
- added new projects menu to the the Project Browser menu bar which shows the project thumbnails and additional infos
- added options to change project thumbnails when rightclicking project widgets at different places in the Prism UI
- added option to change the username and abbreviation from the menu in the Project Browser
- added a new "Add Tasks" dialog, which allows to create multiple tasks to a department at once
- added option to allow creation of predefined tasks only
- added option to open project department settings from the rightclick menu in the "Create Departments" window
- added option to the rightclick menu of the department list in the project settings to edit the selected department
- added multiple improvements to the Texture Library like tabs and folder icons
- added support for changing the OCIO variable dynamically in a Houdini session using the Prism-project and Prism-user environment variables
- added shortcuts in Nuke to create the WritePrism node, to save a new version and to save with comment
- added option to backup scenefiles before starting to render
- custom attributes will be detected and exported automatically now when exporting alembics from Maya
- fixed a bug that the asset search didn't work for assets inside a folder
- fixed a bug that the Prism Houdini Filecache node did not show a warning when the export failed in some cases
- fixed an error when using the "Install HDA" state in Houdini to import.hda files
- fixed a bug that some Prism environment variables were not set correctly when saving a new scene version in Houdini
- fixed a bug that textures with different file extension could be displayed in the same texture stack in the Texture Library
- fixed a bug that omitted assets were displayed in the Texture Library
- fixed a bug that the "execute as previous version" menu in the State Manager contained wrong versions for render and playblast states
- fixed a bug that the context menu opened in the USD quickview when zooming using the alt + right mouse button
- fixed a bug that updating USD references using the import state didn't work correctly
- fixed a bug that could cause Houdini Deadline jobs to stop when the Prism USD plugin was loaded
- fixed a bug that the login dialog could popup multiple times when canceled
- changed the behavior that Prism was asking for the account credentials once a week
- changed the default scenefile layout from "list" to "items"
- changed the "Export stage" checkbox on the USD Export state in Maya to "off" by default
- removed "Projects" menu from from the "Options" menu in the Prism Project Browser
- removed the behavior that the current project paths were added to Maya plugin paths environment variables, but added an option in the User Settings to add these paths (can affect Maya launch time)

## Prism 2.0.0.beta9.3

- added the option to open the "Save Extended" window from the autosave popup by holding CTRL while clicking on "Save new version" (this option will become less hidden in the future)
- departments and tasks in the Project Browser lists are now sorted in the order defined in the project settings
- autoback files ending with.old are not displayed as scenefiles in the Project Browser anymore
- the version padding is now removed from the environment variable $PRISM\_FILE\_VERSION in Houdini
- the date display format in the scenefiles tab and the products tab in the Project Browser are matching now
- added a warning popup when the Prism ZBrush integration gets added to a ZBrush version, which hasn't been launched before
- multiple objects can now be selected and deleted at once from the "Objects" list in export states
- fixed a bug that Maya renders were saved in the wrong folder when the Maya scene contained references in some cases
- fixed a bug that playblasts couldn't be saved as.mp4
- fixed a bug that dragged textures from the Texture Library tab could be dropped into the same location, which caused on error when the current project was on a Windows network path
- fixed a bug that adding/removing departments in the "Create Project" window could have some unexpected behavior

## Prism 2.0.0.beta9.2

- added "access tokens" to share licenses from one account with team members without sharing the account password
- added support for thumbnails of.hdr files in the Media Browser and the Texture Library
- fixed an error caused by USD that it was not possible to write USD files to SMB Windows network drives
- fixed an error in Maya when creating an export state when the current taskname contains invalid characters like spaces
- fixed an error when rightclicking a USD export state when the current scene was not saved in the project
- fixed a bug when opening the Hub multiple times in debug mode
- fixed a bug that is was possible to drag products on network locations to their own version stack in the Project Browser
- it's possible now to create and open the texture folder of an asset through the Texture Library if it doesn't exist yet
- fixed an error when opening the Project Settings window in Resolve when the USD plugin was installed

## Prism 2.0.0.beta9.1

- added support for importing USD files into Blender 3.0+
- added support for exporting USD files from Blender 2.82+
- fixed a few errors in Blender related to invalid execution contexts
- fixed a problem that the EXR preview wasn't working on some computers
- fixed an error when trying to convert exr sequences when the exr preview wasn't working
- fixed multiple problems when connecting Prism to DaVinci Resolve
- fixed an error when exporting Maya objects to USD if stripping namespaces would create conflicts
- fixed a bug that assets couldn't be created in some cases when the project folder structure was changed in specific ways
- fixed an error when dragging textures from the Texture Library into locked Houdini HDAs
- many small fixes and improvements

## Prism 2.0.0.beta9

- added new "Departments" tab in the project settings to configure different departments for shots and assets and define one or more default tasks per department
- added support for Karma Hydra delegate in Prism standalone
- added support for viewing.usdnc files in the standalone Project Browser when the Karma Hydra delegate is enabled
- added support for AMD Readon Pro Render Hydra delegate in Prism standalone
- added support for Arnold Hydra delegate in Prism standalone
- added support for viewing.obj files in the USD viewport in the Project Browser
- added USD tab to the User Setting to manage available Hydra delegates
- added new uninstaller and option to uninstall Prism from the Windows "App & features" list
- added option to copy the filepath for the next product version (in the product version list in the Project Browser)
- added option to copy the filepath for the next media version (in the media version list in the Project Browser)
- added the option to create identifiers in the "Media" tab of the Project Browser
- added a warning popup if the connection window in Resolve gets closed before a connection was established
- added the option to append existing environment variables in the environment tab of the project and user settings by using %variable% in the value of an variable
- added the option to use Houdini environment variables in values of environment variables in the environment tab of the project and user settings, for example $JOB
- added the option "Refresh when switching tabs" to the "Options" menu of the Project Browser
- added option to drag & drop textures directly on the asset in the texture library without creating a subfolder first
- added support for importing.vdb files in Maya using the Arnold Volume object
- updated USD to v21.08 (same version as in Houdini 19)
- improved compression quality for preview images
- improved the progress update display when updating plugins
- fixed an error when launching Maya from the Project Browser when the USD plugin is installed
- fixed a problem that Prism didn't recognized that a Maya scene is inside a Prism project when the scene was opened during Maya startup and had some load errors
- fixed a bug that adding ZBrush exports to USD entity containers didn't work correctly, which could cause errors when opening the Project Browser
- fixed a bug that the version of shot scenefiles were not generated correctly in some cases
- fixed a crash when saving a scene using Prism in Blender 3.0 alpha
- fixed a bug that the framerange of the Prism Filecache node in Houdini was not applied correctly in some cases
- fixed a bug that the timeline was not visible for animated alembic files in the USD viewport
- fixed a bug that states could be created in the State Manager in Houdini when clicking on the "Show available export state types" button in some cases
- fixed a bug in Houdini that the "From Node" menu was not visible when pressing the "Show available export state types" button in some cases
- fixed a bug that it was not possible to drag textures from the texture library into Blender
- fixed an error in the installer when the user has no write permissions for the plugin folder
- fixed a bug in Blender that single frame renders had #### in the filename
- fixed an error when closing the Project Browser when a folder was selected in the Texture Library
- fixed an error when dropping a file into the texture library when an asset folder was selected
- fixed the exr preview in the Project Browser for Blender 2.93 (and all other versions using Python 3.9)
- fixed a bug that in Houdini the framerange of the Prism LOP nodes could only be set in the state settings and not on the nodes
- fixed multiple errors when using Prism nodes in Houdini when no Prism project is active
- fixed an error when trying to save a new version from a scenefile, which was saved manually with a different filename
- fixed a bug that exr image previews in the Project Browser where not refreshed correctly after the exr file got overwritten on disk
- fixed a bug that updating to a different Prism version was not possible in some cases
- fixed an error when opening Blender files, which were saved using a newer Blender versions
- fixed an error when opening the project preset window in some cases
- fixed an error when dragging on the timeslider of the image preview in the Project Browser when the preview is a corrupt exr file
- fixed an error when trying to edit the comment of a scenefile in the Project Browser, which filename doesn't match the Prism naming convention
- fixed an error when saving a new version of a scenefile when the current scene was saved manually under a different name
- fixed an error when using custom export presets in Substance Painter
- removed Fusion plugin
- fixed many more errors and bugs

## Prism 2.0.0.beta8.1

- fixed a bug introduced in beta8 that the "Create Shot" window couldn't be open

## Prism 2.0.0.beta8

- added new plugin for the editorial and color grading tool DaVinci Resolve, see [Resolve Plugin](https://prism-pipeline.com/docs/latest/plugins/Resolve/#plugin-resolve)
- added new plugin for the reference image tool "PureRef", see [PureRef Plugin](https://prism-pipeline.com/docs/latest/plugins/PureRef/#plugin-pureref)
- added support for Multiverse to import and export USD objects in Maya
- added option to copy the path for the next scenefile version to the context menu of the scenefile versions in the Project Browser. This can be used to save files from non supported DCCs into the Prism folder structure.
- added the option to create empty USD files for USD department layers and USD sublayers in the Project Browser
- added option to create USD department layer and sublayer in the products list in the Project Browser
- added support for dragging multiple files at once into the "Identifiers" list in the Media tab of the Project Browser to ingest them into the Prism project
- added autoload option for plugins in the plugin list in the User Settings window
- added "Manage Plugin Paths" window, which allows to enable, disable, add and remove pluginpaths and pluginsearchpaths. This window can be opened from the "Plugins" tab in the Prism User Settings.
- when opening the Project Browser the previously selected entity will be selected now
- USD exports in Maya will now strip namespaces
- improved performance for loading video previews when using Python 3
- the color depth in Blender renders is now defined by the scenesetting instead of the hardcoded value of "16"
- fixed an error in the installer when the Windows documents folder was not at it's default location
- fixed an error when using the Deadline plugin if the deadlinecommand executable couldn't be found
- fixed an error in Houdini when refreshing the product version list in the Project Browser in some cases
- fixed a bug that a wrong media preview could be displayed in some cases in the Project Browser, when switching versions quickly
- fixed a problem that the Maya workspace.mel file wasn't created in some cases
- fixed and error when trying to open Usdview in Python 2 in some cases
- fixed an error when reloading plugins in the User Settings window in Python 2
- fixed a bug that drag&drop files into the product version list in the Project Browser didn't work as expected for USD department layers
- fixed a bug that dragging the media preview in the Project Browser into DJV and some other apps didn't work
- fixed a security issue by switching the server connection from http to https
- fixed an error when opening scenefiles manually when no Prism project is active

## Prism 2.0.0.beta7

- added the option to open Prism projects created with Prism 1.x
- added the option to use python expressions as folder structure templates
- added the option to use prefix and suffix characters in template keys. These characters will be added to the resolved path only if the variable of the key evaluates to a valid value. example: @.(frame)@
- added the option to restore folder structure templates to factory defaults in the project settings
- added option to disable the Prism handling of drag&drop of external files in Houdini. This option is in the "DCC Apps" tab in the User Settings window.
- added the option to import a product into Substance Painter by double clicking it in the Project Browser
- drag&drop files into Houdini will be handled by Houdini now if the Prism Texture Library cannot handle it. Previously the drag&drop was canceled in most cases.
- added the option to use the env variable "PRISM\_HOUDINI\_SKIP\_PRESETS" to not load any Prism nodegraph presets in Houdini
- fixed a problem that the Houdini startup could take several minutes when the Prism USD plugin was enabled in some cases
- changed the default folder structure: "beauty" was removed from the 2d render filepaths
- changed the default folder structure: when no framenumber is used in product-, render- or playblast-files then there won't be a double dot (".." ) in the filename anymore
- fixed an error when trying to omit an asset folder
- added a warning when an exported alembic file from ZBrush doesn't contain valid geometry. For example when a ZBrush version before 2021 is used, which doesn't support Alembic exports.
- fixed a popup warning when exporting.obj files from ZBrush in some cases
- fixed an error when trying to import a product into Substance Painter using the "Import custom files" button in the Project Browser
- fixed an error when accessing the list of existing productnames on the USD Export SOP node in Houdini
- fixed an error when opening the context menu of the media preview in the Project Browser in Nuke when the USD plugin was installed
- fixed an error when trying to export a ShotCam in Maya

## Prism 2.0.0.beta6.1

- added support for Renderman in Houdini
- added option to save new Houdini nodegraph presets
- added a new node in Houdini: "Prism LOP Mute Departments" with options to mute/unmute department layers, which are upstream/downstream to the department of the current scenefile
- added to option to the Prism LOP Import node in Houdini to import a file as reference instead of a layer
- added new option "Detect context from input stage" to the Prism LOP Export and Prism LOP Render node. By default this setting is off, which causes the files to get written to the context of the current scenefile.
- added a popup to update plugins, when they are not matching the current Prism version
- added the option "Refresh current tab only" to the "Options" menu in the Project Browser. By default it's disabled, which causes all tabs to refresh when clicking the refresh button
- refreshing tabs in the Project Browser now keeps the previously selected entities selected
- the Project Browser gets hidden temporarily now when capturing entity or scene previews with a screenshot
- fixed a crash when loading the preview of some specific mp4 files
- fixed a bug that could cause folders to appear multiple times in the texture library
- fixed a bug that ingesting products in the Project Browser could cause an endless freeze
- fixed an error when changing layer versions in the Prism USD Layer Manager
- fixed a bug that "Execute as previous version" didn't work for some state types
- fixed an error when running Prism without gui (e.g. with Deadline) in some cases
- fixed an error when trying to uninstall an unloaded plugin

## Prism 2.0.0.beta5.2

- fixed an error when saving scenefiles in some cases
- fixed an error that could show up after a few minutes when working in a DCC where the Prism autosave popup is not supported
- fixed an error when launching Prism with High DPI mode enabled in some cases

## Prism 2.0.0.beta5.1

- added option to the USD quickview to open the stage in a Houdini viewport, which makes all renderers installed in Houdini available in the quickview including Redshift and Karma
- added Deadline Renderfarm plugin (including support for Houdini Python 3 builds)
- added option to Houdini Prism USD export Sop and Lop node and to the USD export state in Maya to export the geometry as alembic (to be able to import it into Substance Painter for example)
- added option to create VRay materials in Houdini when dragging textures from the Texture Library into the Houdini nodegraph
- added the option to use the environment variable PRISM\_AUTOSAVE\_INTERVAL to specify after how many minutes the autosave popup will appear
- moved the preview loading of videofiles to a separate thread, which gives much better performance in the Project Browser when dealing with video files
- disabled the "always on top" mode for the Prism installer and the "Manage Projects" dialog
- the "Open on startup" setting now gets ignored in Prism standalone
- fixed a problem that exr files had no preview in the Texture Library
- fixed a problem that numpy was required to open the Project Browser in Fusion
- fixed an error when opening Usdview from the standalone Project Browser Usd viewport
- fixed a bug, which could cause the the USD viewport to not initialize correctly when opening the Project Browser and which could cause the whole Project Browser UI to disappear in some cases
- fixed a problem that Prism GUIs were not parented to Houdini GUI if Houdini took a long time to launch
- fixed an error in Maya when creating an export state when the taskname of the current scenefile contains a "-"
- fixed a problem that Prism didn't recognize when the Windows documents folder was changed to a non default location
- fixed an error when selecting a productname in the Project Browser when a versionfolder didn't contain geometry files
- fixed a bug that creating an HDA using the "Save HDA" state failed, when the current scenefile was in an asset context inside an assetfolder
- fixed a problem that scenefileversions were not displayed in the Project Browser when they didn't have a versioninfo.json file
- when dragging textures from the Texture Library into the Houdini nodegraph only material types are displayed, which are available in the current Houdini session
- fixed a bug that in some cases a warning could appear when launching a DCC that the PrismInternals plugin is already loaded
- fixed an error when installing the ZBrush integration in some cases
- fixed a bug that local and global scenefiles where not marked correctly in the Project Browser
- fixed an error when trying to copy a local scenefile to the global project folder
- fixed a bug that the scenefile preview was not saved in some cases after setting it in the preview layout in the Project Browser
- fixed an error in Substance Painter when trying to export textures for multiple texture sets
- fixed a bug that 2d comp renders where saved in the 3d render folder
- removed a popup when the "auto load latest version" checkbox is checked on import states and the latest version folder doesn't contain valid files
- fixed a bug that when caching out a specific version with the Prism filecache node in Houdini, the versionname didn't contain the version padding and was not loaded by the filecache node
- fixed an error when trying to create a new scene version from a Nuke autobackup scene
- fixed an error when trying to import an empty USD file in Maya
- fixed a bug that pressing buttons on the autosave popup could crash the DCC
- fixed a bug that scenefile version ups were saved in the global project folder when the local folder is enabled

## Prism 2.0.0.beta4

- changed the default framerange for states in asset scenes to "Single Frame", in shot scenes to "Shot" and in all other scenes to "Scene"
- added a popup when a new update is available
- udim numbers in texturenames will now have a "." prefix instead of a "\_"
- fixed a bug that the texture export using presets was not working in Substance Painter
- fixed a bug that Substance Painter and Maya crashed when Python 3.9 was installed on the computer
- fixed a problem that renaming the 00\_Pipeline folder in the project setup didn't have the expected result
- fixed a bug that the meta data of playblasts couldn't be displayed in the Project Browser ("Show version info" option in the context menu)
- fixed a display bug that the layout of the meta data dialog for products was messed up
- fixed an error when saving the Project Settings when the USD plugin was loaded after the Prism startup
- fixed an error when using the Texture Library without the Substance Painter plugin
- added a Prism desktop icon during the installation
- fixed a bug that the start frame of an image sequence in the Project Browser was wrong
- fixed several problems related to master product versions and shotcam products
- fixed an error when refreshing media versions in the Project Browser when a master render version existed
- fixed a problem that the plugins were not updated when updating Prism using the installer
- fixed an error when exporting geometry in Houdini using the USD Export state and the default Houdini USD SOP ROP
- fixed an error when rightclicking on export states in the State Manager in some cases
- fixed an error when trying to open Usdview in some cases
- set the USD viewport in the Project Browser to be hidden in Houdini by default
- when creating a USD export state, a Prism USD Export node will be created now instead of a default Houdini export node
- fixed an error when trying to create a new plugin in a folder without write permissions
- changed the default location for new plugins to the user preferences folder
- fixed an error when deleting an import state in the State Manager in Houdini in some cases
- fixed an error in Blender when setting the framerange through Prism when the Blender timeline was not visible

## Prism 2.0.0.beta3

- added UDIM support for the Sustance Painter and Texture Library plugin
- added option to create new sub-folders in the Texture Library
- added option to drop files and folders into the Texture Library
- added support for spaces and other previously invalid characters in comments
- added a warning when trying to render a USD scene without a camera
- added a warning when trying to render and the Husk executable is not defined
- improved login/license management in the installer
- fixed a problem, which could let take Houdini take forever to start when the USD plugin was enabled
- fixed a bug, which caused a wrong popup, when creating custom departments
- fixed an error when trying to unload and load the currently active app plugin from the User Settings window
- fixed an error when dragging the media preview in the Project Browser in some cases
- fixed an error when triggering the autoplay media checkbox in the Project Browser
- fixed an error when double clicking a product version in the standalone Project Browser
- fixed an error when clicking on the "show existing productnames" button on the Prism Filecache node in Houdini
- fixed an error when dropping files into an area in Houdini, which is not a pane
- fixed an error when trying to open the project settings from the User Settings window when no project is active
- fixed an error when trying to create a new version from an autoback scene for some DCCs
- fixed an error when trying to login/logout of the Prism account from inside Houdini
- fixed a bug that USD standalone playblasts were not versioned up
- fixed automatic navigation to media after generating standalone USD playblasts and renders

## Prism 2.0.0.beta2

- added 3dsMax plugin (including support for 3dsMax 2022)
- fix error when clicking on the unlock button in the Hub, when the plugin requires a different license
- fixed a bug that the "Browse" window could open behind the "Manage Projects" window
- fixed a typo in the default project folder structure ("resources")
- added a warning when trying to install the Prism integration to the Houdini installation folder instead of the preferences folder
- added a warning when trying to install the Prism Substance Painter integration to a folder, which doesn't end with "Substance Painter"
- the Prism tray will be launched now after the installation
- fixed a display problem for some Photoshop versions in the installer
- fixed a problem that integrations couldn't be added to write protected locations when installed through the installer
- fixed a bug that the Substance Painter integration wasn't added by the installer
- fixed an error in Houdini when opening a scene when no Prism project is active
- fixed an error when dropping a texture into Houdini when no Prism project is loaded
- fixed an error when adding a playblast to the compare states in the Project Browser
- fixed an error when opening a scene in Substance Painter in some cases
- removed the USD Quickview from the Product Browser in Substance
- fixed an error when loading the Prism USD plugin in Maya 2020 when no Maya USD is installed
- removed some unnecessary warnings when launching Prism in some DCCs
- fixed a bug that the Project Browser was opening in front of the Prism Settings when loading/unloading plugins
- fixed a bug that the "Show Prism tray icon on system startup" was always unchecked when opening the Prism Settings
- fixed a problem that could cause Houdini to crash on startup in some cases

## Prism 2.0.0.beta1

### Updated UI and performance

The Prism UI got updated with a modern stylesheet and a redesigned layout of the Project Browser. Now there are three main tabs, which are "Scenefiles", "Products" and "Media". Plugins can add additional tab, like "Textures" from the Texture Library plugin. The names of some entities have changed in Prism 2.0 to make them more intuitive. "Steps" are renamed to "Departments" and "Categories" are renamed to "Tasks". The new name "Products" stands for all kinds of exports and caches created from scenefiles.

![../_images/new_project_browser.jpg](https://prism-pipeline.com/docs/latest/_images/new_project_browser.jpg)

### Customizable folder structure and naming conventions

Because every project is different there is not one perfect folder structure, which works for all projects. The folder structure and filenames are now fully customizable per project through template paths. They can be accessed during and after the project creation in the project settings window. These templates contain variables encapsulated by "@" symbols. When Prism is saving a file the characters @shot@ will be replaced by the shotname for example. Hover over the questionmark at the right side of a template path to get more information about the required variables.

![../_images/customizable_folder_structure.jpg](https://prism-pipeline.com/docs/latest/_images/customizable_folder_structure.jpg)

### Save and load project presets

Project settings and folder structures can be saved as presets now, which can be used to create new projects.

![../_images/project_presets.jpg](https://prism-pipeline.com/docs/latest/_images/project_presets.jpg)

### Environment variables

Custom environment variables can be defined per user and per project now. They can be used to customize Prism and to develop custom workflow.

![../_images/environment_variables.jpg](https://prism-pipeline.com/docs/latest/_images/environment_variables.jpg)

### Asset/Shot meta data

Custom meta data can be saved to each asset and to each shot to keep track of important data.

![../_images/meta_data.jpg](https://prism-pipeline.com/docs/latest/_images/meta_data.jpg)

### USD plugin

The USD plugin adds support for Pixars Universal Scene Description to Prism, which enabled a powerful and modern way of working with data in a CG project.

See [USD Plugin](https://prism-pipeline.com/docs/latest/plugins/USD/#plugin-usd)

### Texture Library plugin

This plugin lets you manage your textures intuitively. You can ingest new textures directly from Substance Painter or by drag & drop them into the Texture Library. Texture stacks, which can contain multiple maps and UDIMs can be drag \* dropped into Houdini to automatically assemble material setups for different renderers from the given textures.

See [Texture Library Plugin](https://prism-pipeline.com/docs/latest/plugins/Libraries/#plugin-libraries)

### Substance Painter plugin

A new Prism integration into Substance Painter. This let's you save and version your Substance Painter scene and export textures to your project.

See [SubstancePainter Plugin](https://prism-pipeline.com/docs/latest/plugins/Substance%20Painter/#plugin-substancepainter)

### ZBrush plugin

A new Prism integration into ZBrush. With this integration you can save and version your ZBrush projects and export geometry in different formats.

See [ZBrush Plugin](https://prism-pipeline.com/docs/latest/plugins/ZBrush/#plugin-zbrush)

### Many small improvements

There are many smaller improvements added which include:

- support for Blender 2.93/3.0
- support for 3ds Max 2022
- a Prism filecache node in Houdini
- support for submitting Deadline jobs from Houdini Python 3 builds
- and much more.