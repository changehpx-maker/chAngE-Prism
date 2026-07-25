## Hooks

## Overview

Hooks are Python files, which are executed automatically by Prism at specific callback events.

**Hooks are placed in a Prism project in this folder:** `00_Pipeline\Hooks`

The filename should look like this `<callback_name>.py` where "callback\_name" will be replaced with the name of the callback, which should execute the file.

For a list of available callbacks see [here](https://prism-pipeline.com/docs/latest/development/developingPlugins/#available-callbacks).

The file needs to have a function named main, which will be executed by Prism when the callback is triggered. Most callbacks will pass one or more arguments to the `main` function.

Prism needs to restart to register newly created hook files. Subsequent changes to the hook files are taking effect immediately. It's not required to reload or restart Prism after changing a hook file.

## Examples

### Creating additional shot folders

This example will create additional folders everytime a shot gets created. The same can be archived for assets using the `onAssetCreated` callback.

Filename: `onShotCreated.py`

Content:

```python
import os

def main(*args, **kwargs):
    origin = args[0]
    entity = args[1]
    additional_shot_folders = ["audio", "plates", "client_data"]
    shot_path = origin.core.getEntityPath(entity=entity)
    for folder in additional_shot_folders:
        folderpath = shot_path + "/" + folder
        os.makedirs(folderpath)
        print("created folder " + folderpath)
```

### Changing the verbosity of Maya Arnold render jobs on Deadline

This example will set a parameter in the Deadline job settings when an Arnold render job gets submitted from Maya to Deadline. Setting the `ArnoldVerbose` parameter to 3 will cause a more detailed log when the scene gets rendered.

Filename: `sm_render_getDeadlineParams.py`

Content:

```python
def main(origin, dlParams, homeDir):
    # check if hook is called in Maya
    if origin.core.appPlugin.pluginName != "Maya":
        return

    # return if the submitted job is not rendering using Arnold
    if dlParams["pluginInfos"]["Renderer"] != "arnold":
        return

    # set the Arnold Verbosity
    dlParams["pluginInfos"]["ArnoldVerbose"] = 3
```