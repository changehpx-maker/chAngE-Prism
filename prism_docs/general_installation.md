## Installation

For a quickstart installation see the [Getting Started](https://prism-pipeline.com/docs/latest/getting_started/#getting-started) page.

## Windows Installation

Prism can be installed using the provided installer or zip file, which can be downloaded from [here](https://prism-pipeline.com/downloads).

You can also find Prism in this [GitHub repository](https://github.com/PrismPipeline/Prism).

Prism can be installed locally on every workstation in your studio.

No additional installation on a server and no database setup is required.

For a centralized setup see.

### Windows Installer

The installer will install Prism into this folder by default: `C:\Program Files\Prism2`

The installer shouldn't be launched as admin from a non-admin account. It will ask for admin permissions in case it's needed.

The plugin `PrismInternals` and `Hub` will be installed to `C:\ProgramData\Prism2\plugins` by default.

This is the default plugin location. Also all other plugins which will be installed afterwards will go into this folder.

### Windows Zip

The zip file can be extracted in any location on your filesystem.

The setup.bat can be used to create Prism shortcuts in your Windows start menu and on your desktop.

## Linux and Mac Installation

For Linux and Mac we provide setup scripts here: [here](https://prism-pipeline.com/downloads).

This will download Prism and dependencies in a Prism folder in your current working directory.

This folder is fully portable and can be moved to other locations.

Run the prism.sh / prism.command file in the Prism folder to launch Prism.

This will setup Prism with all Free plugins.

The Prism Hub is not available on Linux and Mac yet.

Please contact the support to request download links for the Plus plugins for Linux and Mac.

> [!note] Note
> If you get permission warning after setting up the Prism Plus plugins on Mac, run this command on the Prism root folder: `xattr -r -d com.apple.quarantine <prism_root>`

## Plugins

There is a wide range of available [plugins](https://prism-pipeline.com/docs/latest/plugins/#plugins) to integrate Prism into 3rd party tools and to add specific features to Prism.

Plugins can be downloaded from the Prism [Hub](https://prism-pipeline.com/docs/latest/plugins/Hub/#plugin-hub).

By default plugins will be installed to `C:\ProgramData\Prism2\plugins`.

You can change the plugin install location using the gear button in the Prism Hub.

Alternatively you can use the environment variable `PRISM_DEFAULT_PLUGIN_PATH` to set the default plugin installation path.

It's possible to move a plugin after the installation to a different location.

Prism can load plugins from any custom location. To set the paths where Prism will look for plugins you can add and remove plugin paths in the Prism User Settings -> Plugins by clicking the gear button.

These paths are stored in this file and can be different for every Windows user: `%userprofile%\Documents\Prism2\PluginPaths.json`

Installing a plugin from the Hub will download the plugin into the folder mentioned above and then add the path to the `PluginPaths.json` file.

If you don't see a specific plugin in the plugin list in the Prism User Settings, make sure it was downloaded and the path is added to the `PluginPaths.json`.

You can also use the environment variable `PRISM_PLUGIN_PATHS` to specify plugin paths separated by `;`.

The environment variable `PRISM_PLUGIN_SEARCH_PATHS` allows you to specify folders in which Prism will search the sub-folders for plugins.

## DCC integrations

Some Prism plugins require you to setup the Prism DCC integration after the Prism plugin is installed.

For example after the Houdini and Maya plugin installation Prism will ask you where your Houdini and Maya preferences folders are located. Prism will add some files to these folders so that Prism will be loaded when you launch the DCC.

You can add and remove DCC integrations in the Prism User Settings -> DCC apps.

## User Preferences

Prism will save user preferences into this folder: `%userprofile%\Documents\Prism2`

The environment variable `PRISM_USER_PREFS` can be used to change the default preferences location.

The folder can be deleted to reset the user preferences. The folder and files will be created during the Prism launch if it doesn't exist.

## Silent Install

In some cases you might want to install Prism without interacting with any gui (called silent install).

This can be done by executing the Prism installer with specific arguments.

Run the installer in the Windows Command Prompt with the -h argument to see a full list of available arguments.

The available arguments include:

`--nogui`: run the installer without gui. This argument can be skipped when the "installpath" argument is defined (dft=False)

`--installpath`: the path where Prism will be installed (dft="C:Program FilesPrism2")

`--overwrite`: if the installation folder should be overwritten if it exists already (dft=False)

`--clear-userprefs`: if existing Prism user preferences get deleted if they exist (dft=False)

`--plugins`: list of plugin names to install (dft=\[\])

`--setup-integrations`: if the Prism integration gets added to DCCs (dft=False)

`--postinstall-script`: path to Python script, which gets executed after the installation (dft="")

`--launch`: if the Prism GUI should be launched after the installation (dft=False)

`--username`: the username to be used to login in combination with the password. Login is required for plugin installation. (dft="")

`--password`: the password to be used to login in combination with the username. Login is required for plugin installation. (dft="")

`--accesstoken`: the accesstoken to be used to login. Can be used instead of username and password. Login is required for plugin installation. (dft="")

For example:

`Prism_v2.0.0.exe -h` - will print a list of available arguments

`Prism_v2.0.0.exe --nogui` - will install Prism with default settings

`Prism_v2.0.0.exe --installpath D:/tools/Prism --overwrite --clear-userprefs --plugins Houdini Maya Blender Nuke --setup-integrations --launch --accesstoken 86661421-2850-484f-b664-6012d1f228e1` will install Prism to a custom location, overwrite files if the installpath already exists, will clear existing user preferences, install plugins for Houdini, Maya, Blender and Nuke, will setup the Prism DCC integrations for every DCC, which Prism can detect automatically and then launch the Prism gui.

## Centralized Setup

Prism can be installed in a central location in your studio like a server, which can simplify the maintenance for example when updating or downgrading to a different Prism version.

The disadvantage can be that the launch of Prism can take longer if your network speed is slow.

There are multiple ways to setup Prism in a central location.

One possible way is this:

- download the Prism zip from the website
- extract it and move it to a location on your server
- run the setup.bat to create start menu and desktop shortcuts
- open Prism and navigate to the Hub
- click the gear button and set the default plugin path to a folder on your server
- install any plugins from the Hub which you'd like to use
- on all workstations in your studio set the `PRISM_PLUGIN_PATHS` environment variable to a list of paths where your plugins are installed separated by `;`
- from all workstations in your studio run the setup.bat to create Prism shortcuts (or use an automated solution as in the next section)

## Automate Setup using Python Script

The setup.bat will open a GUI to setup shortcuts, uninstaller and DCC integrations.

Instead of using the GUI it is possible to automate this setup using Python scripts.

The following example mimics the behavior of the setup.bat to setup shortcuts, uninstaller, DCC integrations.

It can also be used to set settings in the Prism User Preferences.

```
import os
import sys

sys.path.append("C:/Program Files/Prism2/Scripts")

import PrismCore
core = PrismCore.create(prismArgs=["noUI"])

# add shortcuts to start menu and desktop
core.setupStartMenu()

# add uninstaller, optional, will ask for admin permissions
core.setupUninstaller()

# add DCC integrations automatically
core.integration.addAllIntegrations()

# add specific DCC integration
core.integration.addIntegration("Maya", r"%s\Documents\maya\2024" % (os.getenv("USERPROFILE")))

# set user settings
core.setConfig("dccoverrides", "Maya_path", r"C:\Program Files\Autodesk\Maya2024\bin\maya.exe", config="user")
core.setConfig("dccoverrides", "Maya_override", True, config="user")
```

## Updates

When new Prism versions are available, Prism will display a popup on the next Prism launch to ask you if you want to update.

This popup will only appear for new "stable" versions, but not for new Prism versions, which are marked as "experimental."

Alternatively you can also update or rollback to an older version in the Prism Hub.

In case you want to disable the update check and the popup, you can set the env var `PRISM_UPDATE_CHECK_ENABLED` to `0`.

> [!note] Note
> The update popup will also show if you have plugins loaded, which are older or newer than the recommended plugin version for the Prism version, which you have installed. When testing new experimental plugin versions it's also recommended to use the env var to turn off the update popup, which would install the recommended plugin version, which might be older than your experimental plugin version.

## Firewall Exceptions

If you are using the online licensing, Prism needs to connect to the Prism servers to login, validate your license and download plugins. In environments with strict firewall rules you might need to whitelist connections to the following domain:

[https://service.prism-pipeline.com](https://service.prism-pipeline.com/) (port 443)

## Anti-Virus warnings (false positives)

Some Anti-Virus tools are reporting a false positive when installing Prism. This is usually because of this file: `C:\Program Files\Prism2\Python311\Prism.exe`

The Prism.exe is a copy of the pythonw.exe in the same folder. It only has a changed filename and a changed icon, which can be the reason that some Anti-Virus tools don't trust the file.

There are two ways to workaround this problem:

1. You can add an exception for this file in your Anti-Virus tool to workaround this problem.
2. You can delete the Prism.exe, duplicate the pythonw.exe and rename it to Prism.exe. This will most likely remove the false positive warning and Prism will work without problem. The only difference with this method is that in some places a Python icon will be visible instead of the Prism icon, for example in the Windows Task Manager.

## Uninstall

You can uninstall Prism from the `Installed apps` list in your Windows settings.

Alternatively you can run `C:\Program Files\Prism2\uninstall.bat`.

The uninstaller let's you choose to remove the Prism files, plugins, Prism DCC integrations and user preferences.

![../../_images/uninstaller.jpg](https://prism-pipeline.com/docs/latest/_images/uninstaller.jpg)

## Troubleshooting

### Prism doesn't start

If Prism doesn't start when using the desktop/startmenu shortcuts, then this is most likely caused by one of these reasons:

1\. An Anti Virus Software prevents the execution of this executable:

`C:\Program Files\Prism2\Python311\Prism.exe`

Check your Anti Virus Software settings and add an exception for this file if needed.

2\. An error during the Prism startup. To find the reason for this error, use this file to start Prism with a command prompt:

`C:\Program Files\Prism2\Tools\prism_gui_with_console.bat`

If the command prompt closes too quickly, you can also open a new Windows command prompt and run the.bat file in there.

If there is any error during the startup, an error message will be visible in the command prompt.

Contact the support with this error message for more details and possible solutions.