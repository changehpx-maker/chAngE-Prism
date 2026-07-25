## Developing Plugins

Developers can create their own Prism plugins to add new features or to change existing Prism features.

When you want to customize a Prism feature it is recommended to do that using a plugin and not by modifying the Prism python scripts directly. This allows you to update your Prism version in the future and keeping your customizations. If you would add your custom code to a official Prism scripts, your code would be lost when you update Prism to a newer version.

Prism comes with a bunch of default plugins, but you can create as many additional plugins as you like. You can also share plugins with other people to give them access to your customizations or added features.

## Creating a new plugin

- Open the Prism User Settings dialog and go to the "Plugins" tab.
- Click on "Plus" icon to open the "Create Plugin" dialog
- Enter a name for your plugin, set the plugintype to "Custom", set your preferred location where the plugin will be saved and press "OK".
- That will open the directory where the scripts from the new plugin are located. There you will see a file `Prism_<PLUGINNAME>_Functions.py`. Open that file in a text editor.
- Add your custom code to the plugin. For example in the `__init__` function you can add this line:

```
self.core.popup("My plugin got loaded!")
```

- Save the file and in the Prism Settings rightclick on your plugin in the pluginlist and select "Reload".
- You will see a popup message now with your message.

## Single File Plugins

The simplest form of a plugin can be a single Python file.

To create a minimal single file plugin you can create a new `MyPlugin.py` file with only 3 lines:

```python
class Prism_MyPlugin:
    def __init__(self, core):
        pass
```

This simple form of a plugin has only these requirements:

- the filename defines the plugin name (e.g. `MyPlugin.py`).
- the class in the file must be named `Prism_` followed by the plugin name.
- the `__init__` function must accept a `core` argument.

It's possible to define the pluginname and the classname using top-level variables in the file.

In this case the filename becomes irrelevant and you can name it anything you like.

Here is an example plugin, which adds a custom menu to the Project Browser:

```python
name = "MyPluginName"
classname = "CustomClassName"

from qtpy.QtWidgets import *

class CustomClassName:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"
        self.core.registerCallback("onProjectBrowserStartup", self.onProjectBrowserStartup, plugin=self)

    def onProjectBrowserStartup(self, origin):
        origin.myMenu = QMenu("My Menu")
        origin.myMenu.addAction("Hello", self.onActionTriggered)
        origin.menubar.addMenu(origin.myMenu)

    def onActionTriggered(self):
        self.core.popup("Hello!")
```

For more example plugins see [here](https://prism-pipeline.com/docs/latest/development/examplePlugins/#exampleplugins).

## Using callbacks

In the above example we saw how we can execute our custom code, when the plugin gets loaded. But in most cases we want to execute custom code, when specific events happen in Prism. For example when a shot gets created or when a scenefile gets saved. To do that we can use callbacks in Prism.

Let's say we want to execute some code when a shot gets created. For this we create a new function in our plugin in the `Prism_<PLUGINNAME>_Functions` class, like this:

```
def onShotCreated(self, *args):
    print(args)
    # custom code here...
    self.core.popup("Custom code executed successfully!")
```

Each callback can have several arguments, which provide information about the event. So we are using \*args to accept all amount of arguments and print them out to see, which information are provided by the callback. In this example we can get the shotname and sequence name from the arguments.

Now that we created our function we need to tell Prism that this function should be called when a shot gets created. To do that we register our function to the `onShotCreated` callback, by adding this line in the `__init__` function at the top of our plugin:

```
self.core.callbacks.registerCallback("onShotCreated", self.onShotCreated, plugin=self)
```

Now we can save the script and reload it in the Prism User Settings. Alternatively we could also restart Prism. When we create a shot now our callback function will be executed.

## Replacing Prism functions at runtime

Sometimes you don't want to simply execute custom code in specific events, but you want to replace a Prism function with your own function to change it's behavior. It is possible to do that from within your plugin at runtime without touching the official Prism scripts. In this example we will change the behavior of the `getAssetDescription` function, so that we can receive the description of our assets from a custom database. This description will be visible for all artists in the Project Browser.

At first we add a `getAssetDescription` function to our plugin, where we can add our code to receive to asset description in a custom way:

```
def getAssetDescription(self, *args):
    assetName = args[0]

    # custom code here...
    description = "This is asset %s" % assetName

    return description
```

Next we want to use our `getAssetDescription` function to replace the default one. For that we need to know where the default function exists in the Prism API, which is in this case: `self.core.entities.getAssetDescription`. We add the following line to the `__init__` function of our plugin:

```
self.core.plugins.monkeyPatch(self.core.entities.getAssetDescription, self.getAssetDescription, self, force=True)
```

The first argument is the function we want to replace, the second argument is the function we want to replace it with, the first argument is a reference to our custom plugin and the `force` argument makes sure that the function gets replaced even if it was already replaced by another plugin.

Now we can save the script, reload our plugin and then we can see the new asset descriptions in the Project Browser.

## Calling a original function after it got replaced

In some cases you might want to execute some code before or after a function is called. If there is a callback available for that function it would be easy to do, but this is not always the case. In that case we can replace the default function with our own one as in the previous example. If we only want to add some code before or after the default function, but not modify the default function itself, we could copy the code of the default function into our custom plugin and add our custom code before or after that code. However it's not a good practice to duplicate code. It can make your plugin quite a bit more complex and if that default function gets updated in future Prism releases then your function might become incompatible.

A better solution is to replace the default function with your custom function, but from your custom function you call the original function, which got replaced. That way you can easily add code before or after the original function gets called and modify the input arguments or the return values if required.

In this example we want to change which shots are visible in the Project Browser, by filtering all shots, which have "test" in their shotname. The best way to do that is to modify the return value of the `getShots` function.

To do that we add this line in the `__init__` function of our plugin:

```
self.core.plugins.monkeyPatch(self.core.entities.getShots, self.getShots, self, force=True)
```

And then we add this function in our plugin:

```
def getShots(self, *args, **kwargs):
    sequences, shots = self.core.plugins.callUnpatchedFunction(self.core.entities.getShots, *args, **kwargs)
    shots = [shot for shot in shots if "test" not in shot["shot"]]
    return sequences, shots
```

After saving our script and reloading our plugin we won't see any shots with "test" in their name in the Project Browser anymore.

## Example code

Here is the full script of the `Prism_<PLUGINNAME>_Functions.py` file with all the above examples for reference:

```
from PrismUtils.Decorators import err_catcher_plugin as err_catcher

class Prism_<PLUGINNAME>_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.core.callbacks.registerCallback("onShotCreated", self.onShotCreated, plugin=self)
        self.core.plugins.monkeyPatch(self.core.entities.getAssetDescription, self.getAssetDescription, self, force=True)
        self.core.plugins.monkeyPatch(self.core.entities.getShots, self.getShots, self, force=True)

    @err_catcher(name=__name__)
    def isActive(self):
        return True

    def onShotCreated(self, *args):
        print(args)
        # custom code here...
        self.core.popup("Custom code executed successfully!")

    def getAssetDescription(self, *args):
        assetName = args[0]

        # custom code here...
        description = "This is asset %s" % assetName

        return description

    def getShots(self, *args, **kwargs):
        sequences, shots = self.core.plugins.callUnpatchedFunction(self.core.entities.getShots, *args, **kwargs)
        shots = [shot for shot in shots if "test" not in shot["shot"]]
        return sequences, shots
```

## Including additional Python modules in plugins

Some plugins require additional Python modules, which are not included in the Prism Core modules.

These modules can be placed under the plugin root folder in an `ExternalModules/Python3` folder.

In the `__init__` function of the plugin in the `Prism_<PLUGINNAME>_Functions.py` file, this needs to be added in order to let Python import modules from that folder:

```
extModPath = os.path.join(self.pluginDirectory, "ExternalModules", "Python3")
sys.path.append(extModPath)
```

This approach is also used by many official Prism plugins.

## Available callbacks

This is a WIP list of all callbacks, which are available in the current Prism version. If you require additional callbacks please contact the support.

- `onCreateAssetDlgOpen`
- `onCreateAssetDlgTypeChanged`
- `onCreateProjectOpen`
- `postInitialize`
- `getIconPathForFileType`
- `preSaveScene`
- `postSaveScene`
- `getScenefilePaths`
- `sceneSaved`
- `onPrismSettingsOpen`
- `prismSettings_loadUI`
- `prismSettings_saveSettings`
- `onPrismSettingsSave`
- `prismSettings_loadSettings`
- `trayContextMenuRequested`
- `trayIconClicked`
- `openTrayContextMenu`
- `onProjectSettingsOpen`
- `projectSettings_loadUI`
- `preProjectSettingsSave`
- `postProjectSettingsSave`
- `preProjectSettingsLoad`
- `postProjectSettingsLoad`
- `onSaveExtendedOpen`
- `onGetSaveExtendedDetails`
- `onSetProjectStartup`
- `onDependencyViewerOpen`
- `onShotDlgOpen`
- `onEditShotDlgSaved`
- `onEditShotDlgLoaded`
- `onEntityWidgetCreated`
- `onAssetDlgOpen`
- `projectBrowser_getAssetMenu`
- `projectBrowser_getShotMenu`
- `onMediaBrowserOpen`
- `mediaBrowserContextMenuRequested`
- `openPBListContextMenu`
- `onCreateIdentifierDlgOpen`
- `onCreateVersionDlgOpen`
- `onCreateAovDlgOpen`
- `onProductBrowserOpen`
- `productSelectorContextMenuRequested`
- `onCreateProductDlgOpen`
- `productVersionAdded`
- `onProjectBrowserStartup`
- `onProjectBrowserShow`
- `projectBrowser_loadUI`
- `onProjectBrowserClose`
- `onProjectBrowserRefreshUI`
- `projectBrowserContextMenuRequested`
- `sceneBrowserContextMenuRequested`
- `sceneBrowserContextMenuRequested`
- `openPBFileContextMenu`
- `onSceneOpen`
- `preLoadPresetScene`
- `postLoadPresetScene`
- `onDepartmentDlgOpen`
- `onTaskDlgOpen`
- `onStateManagerOpen`
- `onStateManagerClose`
- `onStateCreated`
- `onStateDeleted`
- `onStateManagerShow`
- `prePublish`
- `postPublish`
- `preExport`
- `postExport`
- `preRender`
- `postRender`
- `preImport`
- `postImport`
- `prePlayblast`
- `postPlayblast`
- `postIntegrationAdded`
- `onIdentifierCreated`
- `onVersionCreated`
- `onAovCreated`
- `onPluginsLoaded`
- `pluginLoaded`
- `onProductCreated`
- `onAssetFolderCreated`
- `onAssetCreated`
- `onShotCreated`
- `onDepartmentCreated`
- `onTaskCreated`
- `getPresetScenes`
- `onSceneFromPresetCreated`
- `onProjectChanged`
- `updatedEnvironmentVars`
- `expandEnvVar`
- `onProjectCreated`
- `onStateStartup`