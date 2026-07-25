## Communicate between Prism instances

## Overview

Prism can be launched as a standalone application or inside of DCCs.

When you're working in multiple DCCs at the same time, there will be multiple Prism instances running on your computer simultaneously.

By default these Prism instances are independent from each other and don't communicate with each other.

It is possible to enable this communication to allow a button click in one DCC to trigger an event in another DCC.

This can used for example to create a single button, which exports and object from one DCC and then automatically imports it into another DCC.

To make use of this feature, some basic Python knowledge is required.

## Setup

To enable this feature go the the Prism User Settings in the "Miscellaneous" tab and check the "Socket Communication" option.

Then restart Prism and your DCCs.

## Sending Python Commands

Inside of your DCC you can use the Prism Python API to send a Python script command to a Prism instance inside of an open DCC.

For that you can use the sendCmd function of the PrismInternals plugin. This function takes the target DCC name as a first argument and the Python code as a string as the second argument.

This example will open a popup inside of Houdini:

```
cmd = """
import PrismInit
PrismInit.pcore.popup("Hello Houdini")
"""
pcore.getPlugin("PrismInternals").internals.sendCmd("Houdini", cmd)
```

You can run this example in the Maya script editor or in any Python shell where you have access to a PrismCore instance.

## Example: Send object from Maya to Houdini with one click

In this example we'll create a Maya shelf button, which will export the currently selected Maya object as an alembic file and then import this alembic file into Houdini. All with one click on the shelf button.

In Maya open the shelf editor to create a new shelf tool.

In the "Command" tab change the language to Python and paste the following code:

```
import maya.cmds as cmds

def exportMayaObjects():
    # get selected objects
    objs = cmds.ls(selection=True, long=True)

    # get Prism State Manager
    sm = pcore.getStateManager()

    # create export state
    state = sm.createState("Export")

    # set objects to export
    state.ui.addObjects(objs)

    # export objects
    sm.publish(states=[state], successPopup=False, incrementScene=False)
    path = state.ui.l_pathLast.text()
    return path

def importHoudiniObjects(path):
    cmd = """
import hou
import PrismInit
import win32com.client
import win32gui, win32con

pcore = PrismInit.pcore

# create a Prism Import SOP
node = hou.node("/obj/geo/quick_import")
if not node:
    node = hou.node("/obj/geo1").createNode("prism::ImportFile", "quick_import")

node.setDisplayFlag(True)
node.setRenderFlag(True)
pcore.appPlugin.goToNode(node)

# get the state of the node
state = node.hdaModule().getState({"node": node})

# set the importpath
state.ui.setImportPath(\"%s\")
state.ui.importObject()

# bring the Houdini to the front
window = hou.qt.mainWindow()
window.showMaximized()
window.activateWindow()
window.raise_()

# minimize the Maya window
winId = win32gui.GetForegroundWindow()
fgTitle = win32gui.GetWindowText(winId)
if "Autodesk MAYA" in fgTitle:
    win32gui.ShowWindow(winId, win32con.SW_MINIMIZE)
    """ % path.replace("\\", "/")
    pcore.getPlugin("PrismInternals").internals.sendCmd("Houdini", cmd)

path = exportMayaObjects()
importHoudiniObjects(path)
```

Make sure your scenefile is saved under an asset or shot in your Prism project.

Now create and select some objects in the Maya viewport and press the shelf button.

The objects gets exported from Maya, imported into Houdini and then the Maya window will be minimized so that you can see object in Houdini.

## Example: Send object from Houdini to Maya with one click

In this example we'll create a Houdini shelf button, which will export the currently selected Houdini node as an alembic file and then import this alembic file into Maya. All with one click on the shelf button.

In Houdini create a new tool on a shelf.

In the "Script" tab paste the following code:

```
import maya.cmds as cmds

def exportMayaObjects():
    # get selected objected
    objs = cmds.ls(selection=True, long=True)

    # get Prism State Manager
    sm = pcore.getStateManager()

    # create export state
    state = sm.createState("Export")

    # set objects to export
    state.ui.addObjects(objs)

    # export objects
    sm.publish(states=[state], successPopup=False, incrementScene=False)
    path = state.ui.l_pathLast.text()
    return path

def importHoudiniObjects(path):
    cmd = """
import hou
import PrismInit
import win32com.client
import win32gui, win32con

pcore = PrismInit.pcore

# create a Prism Import SOP
node = hou.node("/obj/geo/quick_import")
if not node:
    node = hou.node("/obj/geo1").createNode("prism::ImportFile", "quick_import")

node.setDisplayFlag(True)

# get the state of the node
state = node.hdaModule().getState({"node": node})

# set the importpath
state.ui.setImportPath(\"%s\")
state.ui.importObject()

# bring the Houdini to the front
window = hou.qt.mainWindow()
window.showMaximized()
window.activateWindow()
window.raise_()

# minimize the Maya window
winId = win32gui.GetForegroundWindow()
fgTitle = win32gui.GetWindowText(winId)
if "Autodesk MAYA" in fgTitle:
    win32gui.ShowWindow(winId, win32con.SW_MINIMIZE)
    """ % path.replace("\\", "/")
    pcore.getPlugin("PrismInternals").internals.sendCmd("Houdini", cmd)

path = exportMayaObjects()
importMayaObjects(path)
```

Make sure your scenefile is saved under an asset or shot in your Prism project.

Now create and select a node in the geometry context in Houdini and press the shelf button.

The node gets exported from Houdini, imported into Maya and then the Houdini window will be minimized so that you can see object in Maya.