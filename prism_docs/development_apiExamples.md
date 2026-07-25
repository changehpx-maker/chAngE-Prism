## Scripting API examples

The Prism python scripting API can be used to customize various features of Prism and trigger actions. Almost every feature, which is available through the GUI can be accessed by external python scripts. Below there is a list of examples:

## General

**Create a new Prism instance:**

```
import sys
sys.path.append("C:/Program Files/Prism2/Scripts")

import PrismCore
core = PrismCore.create(prismArgs=["noUI"])

# use this if you want to load the previously active project
core = PrismCore.create(prismArgs=["noUI", "loadProject"])

# use this is you want to show the GUI
# core = PrismCore.show(prismArgs=["loadProject"])

print(core.version)
```

**Create a new project:**

```
name = "My Project Name"
path = "D:/Projects/myProject"
core.projects.createProject(name, path, preset="Default")
```

**Change the active project:**

```
path = "D:/Projects/myProject"
core.changeProject(path)

print(core.projectName)
print(core.projectPath)
```

**Create an assetfolder:**

```
entity = {
    "type": "assetFolder",
    "asset_path": "MyFolder"
}
core.entities.createEntity(entity)
```

**Create an asset:**

```
entity = {
    "type": "asset",
    "asset_path": "MyFolder/MyAssetName"
}
core.entities.createEntity(entity)
```

**Create a shot:**

```
entity = {
    "type": "shot",
    "sequence": "a",
    "shot": "0010",
}
frameRange = [1001, 1040]
core.entities.createEntity(entity, frameRange=frameRange)
```

**Create a department:**

```
entity = {
    "type": "shot",
    "sequence": "a",
    "shot": "0010",
}
department = "fx"

core.entities.createDepartment(department, entity, createCat=False)
```

**Create a task:**

```
entity = {
    "type": "shot",
    "sequence": "a",
    "shot": "0010",
}
department = "fx"
task = "fire"

#  this function might get renamed in future versions
core.entities.createCategory(entity, department, task)
```

**Create a scenefile from a preset:**

```
entity = {
    "type": "shot",
    "sequence": "a",
    "shot": "0010",
}
department = "fx"
task = "fire"

#  get all available preset of the current project
presets = core.entities.getPresetScenes()

#  get the first preset, which is a Houdini scenefile
fileName = [f for f in presets if f.endswith(".hip")][0]

core.entities.createSceneFromPreset(
    entity,
    fileName,
    department,
    task,
    comment="high speed",
)
```

## Getting Existing PrismCore Instance

Inside of a DCC you can use the existing PrismCore instance to access the Prism Python API.

This is preferred over creating a new PrismCore instance.

Inside of Blender, Houdini, Maya and Substance Painter

```
import PrismInit
core = PrismInit.pcore
```

Inside of 3dsMax, Nuke and Unreal Engine the PrismCore instance is defined globally in the `pcore` variable.

## Prism Account Login

**Login with Password:**

```
plugin = core.getPlugin("PrismInternals")
plugin.internals.login(user="myUser", password="myPw")
```

**Login with Access Token:**

See [Access Token](https://prism-pipeline.com/docs/latest/general/licensing/#using-access-tokens) for more details.

```
plugin = core.getPlugin("PrismInternals")
plugin.internals.login(accessToken="myAccessToken")
```

**Logout:**

```
plugin = core.getPlugin("PrismInternals")
plugin.internals.logout()
```

## Managing Plugins

**Check if a plugin is loaded:**

```
pluginName = "USD"
plugin = core.plugins.getPlugin(pluginName)
isLoaded = plugin is not None
if isLoaded:
    print("plugin %s is loaded from path: %s" % (pluginName, plugin.pluginPath)
```

**Load a plugin:**

```
# by name
core.plugins.loadPlugin(name="USD")

# by path
core.plugins.loadPlugin(path="C:/path/to/plugin/USD")
```

**Check if a pluginpath is in the plugin config and can be loaded, if not add it to the config:**

```
pluginPath = "C:/path/to/plugin/USD"
if not core.plugins.canPluginBeFound(pluginPath):
    core.plugins.addToPluginConfig(pluginPath=pluginPath)
```

**Remove a pluginpath from the plugin config, so it won't get loaded:**

```
pluginPath = "C:/path/to/plugin/USD"
core.plugins.removeFromPluginConfig(pluginPath=pluginPath)
```

**Install a Plugin:**

```
core.getPlugin("PrismInternals").internals.installPlugin("Houdini")
```

**Uninstall a Plugin:**

```
plugin = core.getPlugin("Houdini")
core.getPlugin("PrismInternals").internals.uninstallPlugin(plugin)
```

**Add a DCC integration:**

```
import os
path = os.environ["USERPROFILE"] + "/Documents/houdini19.5"
core.integration.addIntegration("Houdini", path=path)
```

**Remove a DCC integration:**

```
import os
path = os.environ["USERPROFILE"] + "/Documents/houdini19.5"
core.integration.removeIntegration("Houdini", path=path)
```

## Libraries

**Ingest textures:**

```
# getting the plugin instance
plugin = core.getPlugin("Libraries")

# specifying the texture paths
textures = [
    "D:/test.jpg",
    "D:/test2.jpg"
]

# specifying the location. Available options are the items in the location dropdown in the Texture Library window
location = "Assets"

# specifying the assetname including assetfolders
asset = {"type": "asset", "asset_path": "MyFolder/MyAssetName"}

# specifying subfolders where the files will be copied to
subfolders = "proxies/v0001"

# ingesting the textures into the project
plugin.ingestTextures(textures, location, asset=asset, subfolders=subfolders)

# adding textures to the project library instead to a specific asset
location = "Project Library"
plugin.ingestTextures(textures, location, subfolders=subfolders)
```

## Project Management

**Set manager for project:**

```
# getting the plugin instance
plugin = core.getPlugin("ProjectManagement")

# set manager and
core.setConfig("prjManagement", "manager", val="Shotgrid", config="project")
core.setConfig("prjManagement", "shotgrid_url", val="https://mystudio.shotgrid.autodesk.com", config="project")
core.setConfig("prjManagement", "shotgrid_projectName", val="MySgProject", config="project")

# reload current project to refresh all settings and trigger Shotgrid login
core.changeProject(core.projectPath)
```

## Studio

**Add project to studio:**

```
# getting the plugin instance
plugin = core.getPlugin("Studio")

# getting the path to the project config
projectPath = "C:/projects/projectA"
cfgPath = core.configs.getProjectConfigPath(projectPath)

# adding the config path to the studio settings
plugin.addProjectToStudio(cfgPath)
```

**Assign user to project:**

```
# getting the plugin instance
plugin = core.getPlugin("Studio")

# getting username and project config path
user = core.username
projectPath = "C:/projects/projectA"
cfgPath = core.configs.getProjectConfigPath(projectPath)

# getting currently assigned project for the user
currentAssignments = plugin.getProjectsForUser(user)

# getting a list of project configs of the assigned projects
currentAssignments = [assignment["configPath"] for assignment in currentAssignments]

# check if the user is already assigned to the project
if cfgPath not in currentAssignments:
    # add the projects to the current assignments
    assignments = currentAssignments
    assignments.append(cfgPath)
    plugin.setProjectsAssignedToUsers(users=[user], projects=assignments)
```

## USD

**Generate the productpath for an entity USD file**

```
# getting the plugin instance
plugin = core.getPlugin("USD")

# define asset
entity = {"type": "asset", "asset_path": "chars/dog"}

# generate filepath for entity USD file
entityUsdFilepath = plugin.api.getNewEntityUsdPath(entity=entity)
```

**Generate the productpath for an USD department layer**

```
# getting the plugin instance
plugin = core.getPlugin("USD")

# define asset and department
entity = {"type": "asset", "asset_path": "chars/dog"}
department = "mod"

# generate filepath for department layer
departmentUsdFilepath = plugin.api.getNewDepartmentLayerPath(entity=entity, department=department)
```

**Generate the productpath for an USD department sublayer**

```
# getting the plugin instance
plugin = core.getPlugin("USD")

# define asset, department and sublayer
entity = {"type": "asset", "asset_path": "chars/dog"}
department = "mod"
sublayer = "baseGeo"

# generate filepath for department layer
sublayerUsdFilepath = plugin.api.getNewSublayerPath(entity=entity, department=department, sublayer=sublayer)
```

**Set department layer in entity USD file**

```
# getting the plugin instance
plugin = core.getPlugin("USD")

departmentUsdFilepath = "C:\\projects\\film\\03_Production\\Assets\\chars\\dog\\products\\_layer_mod_master\\v0001\\dog__layer_mod_master_v0001.usda"
plugin.api.updateDepartmentLayerInCurrentEntityUSD(departmentUsdFilepath)
```

**Set sublayer layer in department layer**

```
# getting the plugin instance
plugin = core.getPlugin("USD")

sublayerUsdFilepath = "C:\\projects\\film\\03_Production\\Assets\\chars\\dog\\products\\_layer_mod_baseGeo\\v0001\\dog__layer_mod_baseGeo_v0001.usda"
plugin.api.updateLayerInDepartmentLayer(sublayerUsdFilepath)
```