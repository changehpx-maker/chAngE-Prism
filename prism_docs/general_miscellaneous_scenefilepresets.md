## Creating Scenefile Presets

Prism provides an empty scenefile preset for each DCC.

You can create a new scenefile from a preset from the context menu in the Scenefiles list in the Project Browser.

To create custom presets you can setup a scenefile in your DCC with your desired content and then open the Project Browser within your DCC -> right click in the Scenefile list -> Create new version from preset -> < Create new preset from current >.

The created preset will then appear in the "Create new version from preset" menu.

![../../../_images/scenefilepresets.png](https://prism-pipeline.com/docs/latest/_images/scenefilepresets.png)

The custom preset scenes are then stored inside the respective project "PROJECTPATH00\_PipelinePresetScenes".

The default "EmptyScene" presets are stored in the Prism plugins folder inside the respective plugin. Usually in ProgramData folder, for example: `%PROGRAMDATA%\Prism2\plugins\Nuke\Presets`

It's not recommended to modify the default empty presets in the plugin folder, because any changes will be lost when updating the plugin to a newer version in the future.

Instead you can set the env var `PRISM_SHOW_DEFAULT_SCENEFILE_PRESETS` to `0` and then create your own presets in your project folder.

> [!note] Note
> The env var `PRISM_SHOW_DEFAULT_SCENEFILE_PRESETS` is available in Prism v2.0.18 and newer.

You can also use the env var `PRISM_SCENEFILE_PRESET_PATHS` to define folders in which Prism will look for scenefile presets.

This can be useful to create studio wide presets, which are not specific to a single project.

To automatically create a scenefile version from a preset, when a specific task gets created, use the `Preset Scenes` category in your project settings.

> [!note] Note
> The `Preset Scenes` category is only available with a Prism Plus or Pro license.