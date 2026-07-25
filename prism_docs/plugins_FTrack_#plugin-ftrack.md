![[Logo: FTrack]](https://prism-pipeline.com/docs/latest/_static/banner_logos/ftrack_logo.png)

## FTrack

The FTrack plugin connects Prism to [FTrack](https://www.ftrack.com/), a project management tool focused on VFX and animation projects.

## Overview

Using this plugin artists can publish media from Prism to FTrack, see their assigned tasks in Prism and more. To use this plugin the following prerequisites are required:

- an active FTrack site (either a payed site or a free trial site)
- the "ProjectManagement" Prism plugin needs to be installed and loaded.

The FTrack plugin has the following features:

- display FTrack assets, shots and tasks in Prism
- publish media and product versions to FTrack
- view and set the FTrack status of tasks, product versions and media version
- create and view notes and replies on tasks, product versions and media versions
- view assigned tasks in the Project Browser
- open the FTrack page of any entity in a webbrowser directly from Prism

Note: The Prism FTrack plugin works with Python 3 only, because of the requirements of the latest official FTrack API.

## Setup

To activate the FTrack plugin for your currently active Prism project open the Prism Project Settings window and go the the "Project Management" tab. In the "Manager" dropdown select "FTrack". Next press the "Setup" button, which will guide you through a setup process, in which you have to enter your FTrack URL and your account credentials to login.

After Prism logged in successfully in the setup dialog, you will see a list of your existing FTrack projects. Select the one you want to connect to Prism and click next.

On the next page you can select to which Prism project you want to connect it to. In most cases this will be your current Prism project, which is the first one in the list, which is already selected.

Click next and now Prism is downloading the thumbnails of your assets and shots. That can take a few seconds depending on how much entities there are in your FTrack project.

Once the setup is completed the FTrack URL and the project name are added to the Prism Project Settings window. The User account credentials can be accessed in the "Project Management" tab of the Prism User Settings.

You can customize the statuses, which can be assigned to tasks, product versions and media versions in the Prism Project Settings, but these statuses should always be named the same as in FTrack.

## Assets, Shots and Tasks

In the "Scenefiles" tab of the Prism Project Browser you can view all assets, shots, departments and tasks, which exists in FTrack. The thumbnails, description (for assets) and the framerange (for shots) will be synced from FTrack as well. The folders of the tasks might not exist in your Prism project folder yet, but as soon as a scenefiles gets saved under a task, all the required folders will be created.

FTrack assets need to have the "Asset Build" type in order to be recognized by Prism. FTrack shots need to have the "Shot" type and need to be in a folder, which represents the sequence.

Assets and shots have to be created in FTrack and cannot be created inside Prism if the FTrack plugin is active. Departments and tasks have to be created in FTrack as well by default, but in the Prism project settings you can enable the creation of local departments and tasks, which don't exist in FTrack.

If you have any assets, shots, tasks, product versions or media versions in FTrack, which you don't want to be visible inside Prism, you can create a boolean custom attribute named "noPrism" in FTrack on your entity and set it to "True".

You can rightclick any asset, shot or task and open it's page in FTrack in a webbrowser.

Tasks have a status icon before the name and a tooltip with the status name. This status can be changed from the rightclick menu or in FTrack.

You can also access FTrack notes on a task from the "Show Notes..." option in the rightclick menu of a task. This opens a window, where you can view and create FTrack notes and replies.

To view the FTrack tasks, which are assigned to the currently loggedin user, you can open the "Tasks" tab in the Prism Project Browser. Here you can see a list of all your assigned tasks, as well as their status and their start/end dates. You can filter the displayed tasks by their status using the checkboxes at the bottom of the page. On the right side you can view and create notes for the currently selected task. You can doubleclick a task item to jump directly to the scenefiles of this task.

## Product versions

Product versions can be published from the "Products" tab in the Prism Project Browser to FTrack. The product file itself will not be uploaded. Instead Prism will create a version entity in FTrack with the local filepath attached to it. After a product version is published to FTrack, the status for the product versions can be set and notes can be viewed/created from the rightclick menu of the version.

If a product version is getting published to FTrack, it will be created on the task, which matches the product name in Prism. If no matching task is found in FTrack Prism will ask you to select a FTrack task from a list, to which one the version will be published. In the Prism Project Settings this option can be disabled ("Allow publishes from non-existent tasks").

## Media versions

Media versions like renders and playblasts can be published from the "Media" tab in the Prism Project Browser to FTrack using the rightclick menu on the media thumbnail or the version item. Prism will create a version entity in FTrack with the local filepath attached to it. Optionally you can also add a description and let Prism upload a proxy version of your media, which can be reviewed inside of FTrack. After a media version is published to FTrack, the status for the media versions can be set and notes can be viewed/created from the rightclick menu of the version.

If a media version is getting published to FTrack, it will be created on the task, which matches the identifier name in Prism. If no matching task is found in FTrack Prism will ask you to select a FTrack task from a list, to which one the version will be published. In the Prism Project Settings this option can be disabled ("Allow publishes from non-existent tasks").

## Memory Caching

Prism queries assets, shots, tasks and more directly from FTrack when required. Sending a lot of requests to FTrack can become very slow, which is why Prism caches requests in memory to avoid the same requests in the future. For example: When you click a shot in the "Scenefiles" tab in the Project Browser, Prism will requests a list of all tasks of that shot from FTrack and saves it in a memory cache. When you select the same shot again later on, Prism will use tasklist, which is stored in the cache instead of sending a new requests to FTrack. In some cases it is needed to clear the memory cache, for example if someone is creating a new task in FTrack, but the list of tasks for that shot is already cached in a memory in Prism. Without clearing the cache, the new task won't be visible inside Prism. To clear the cache you can press the refresh icon in the Project Browser, restart Prism or you can use the "Clear Cache" option in the "FTrack" menu in the Prism Project Browser.

## Environment Variables

The ftrack plugin can be controlled using the following environment variables:

| Name | Description |
| --- | --- |
| PRISM\_FTRACK\_URL | Sets the ftrack URL, which Prism connects to. This overrides the URL in the project settings. (e.g. [https://company.ftrackapp.com](https://company.ftrackapp.com/)) |
| PRISM\_FTRACK\_EMAIL | The email to use for the login. (e.g. [john@company.com](mailto:john%40company.com)) |
| PRISM\_FTRACK\_APIKEY | The api key to use for the login. (e.g. key123) |
| PRISM\_FTRACK\_ASSET\_BASEPATH | A foldername or path to sync only assets at a specific path in ftrack to Prism (e.g. Assets/Characters) |