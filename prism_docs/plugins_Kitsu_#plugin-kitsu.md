![[Logo: Kitsu]](https://prism-pipeline.com/docs/latest/_static/banner_logos/kitsu_logo.png)

## Kitsu

The Kitsu plugin connects Prism to [Kitsu](https://www.cg-wire.com/kitsu), a project management tool focused on VFX and animation projects.

## Overview

Using this plugin artists can publish media from Prism to Kitsu, see their assigned tasks in Prism and more. To use this plugin the following prerequisites are required:

- an active Kitsu site (either a payed site or a self hosted site)
- the "ProjectManagement" Prism plugin needs to be installed and loaded.

The Kitsu plugin has the following features:

- display Kitsu assets, shots and tasks in Prism
- publish media and product versions to Kitsu
- view and set the Kitsu status of tasks, product versions and media version
- create and view notes and replies on tasks, product versions and media versions
- view assigned tasks in the Project Browser
- open the Kitsu page of any entity in a webbrowser directly from Prism

## Setup

To activate the Kitsu plugin for your currently active Prism project open the Prism Project Settings window and go the the "Project Management" tab. In the "Manager" dropdown select "Kitsu". Next press the "Setup" button, which will guide you through a setup process, in which you have to enter your Kitsu URL and your account credentials to login.

After Prism logged in successfully in the setup dialog, you will see a list of your existing Kitsu projects. Select the one you want to connect to Prism and click next.

On the next page you can select to which Prism project you want to connect it to. In most cases this will be your current Prism project, which is the first one in the list, which is already selected.

Click next and now Prism is downloading the thumbnails of your assets and shots. That can take a few seconds depending on how much entities there are in your Kitsu project.

Once the setup is completed the Kitsu URL and the project name are added to the Prism Project Settings window. The User account credentials can be accessed in the "Project Management" tab of the Prism User Settings.

You can customize the statuses, which can be assigned to tasks, product versions and media versions in the Prism Project Settings, but these statuses should always be named the same as in Kitsu.

## Assets, Shots and Tasks

In the "Scenefiles" tab of the Prism Project Browser you can view all assets, shots, departments and tasks, which exists in Kitsu. The thumbnails, description (for assets) and the framerange (for shots) will be synced from Kitsu as well. The folders of the tasks might not exist in your Prism project folder yet, but as soon as a scenefiles gets saved under a task, all the required folders will be created.

Assets and shots have to be created in Kitsu and cannot be created inside Prism if the Kitsu plugin is active. Departments and tasks have to be created in Kitsu as well by default, but in the Prism project settings you can enable the creation of local departments and tasks, which don't exist in Kitsu.

If you have any assets, shots, tasks, product versions or media versions in Kitsu, which you don't want to be visible inside Prism, you can create a boolean custom attribute named "noPrism" in Kitsu on your entity and set it to "True".

You can rightclick any asset, shot or task and open it's page in Kitsu in a webbrowser.

Tasks have a status icon before the name and a tooltip with the status name. This status can be changed from the rightclick menu or in Kitsu.

You can also access Kitsu notes on a task from the "Show Notes..." option in the rightclick menu of a task. This opens a window, where you can view and create Kitsu notes and replies.

To view the Kitsu tasks, which are assigned to the currently loggedin user, you can open the "Tasks" tab in the Prism Project Browser. Here you can see a list of all your assigned tasks, as well as their status and their start/end dates. You can filter the displayed tasks by their status using the checkboxes at the bottom of the page. On the right side you can view and create notes for the currently selected task. You can doubleclick a task item to jump directly to the scenefiles of this task.

## Product versions

Product versions can be published from the "Products" tab in the Prism Project Browser to Kitsu. The product file itself will not be uploaded. Instead Prism will create a comment on the task entity in Kitsu with the local filepath attached to it. After a product version is published to Kitsu, the status for the product versions can be set and notes can be viewed/created from the rightclick menu of the version in Prism.

If a product version is getting published to Kitsu, it will be created on the task, which matches the product name in Prism. If no matching task is found in Kitsu Prism will ask you to select a Kitsu task from a list, to which one the version will be published. In the Prism Project Settings this option can be disabled ("Allow publishes from non-existent tasks").

## Media versions

Media versions like renders and playblasts can be published from the "Media" tab in the Prism Project Browser to Kitsu using the rightclick menu on the media thumbnail or the version item. Prism will create a comment entity in Kitsu with the local filepath attached to it. Optionally you can also add a description and let Prism upload a proxy version of your media, which can be reviewed inside of Kitsu. After a media version is published to Kitsu, the status for the media versions can be set and notes can be viewed/created from the rightclick menu of the version.

If a media version is getting published to Kitsu, it will be created on the task, which matches the identifier name in Prism. If no matching task is found in Kitsu Prism will ask you to select a Kitsu task from a list, to which one the version will be published. In the Prism Project Settings this option can be disabled ("Allow publishes from non-existent tasks").

## Memory Caching

Prism queries assets, shots, tasks and more directly from Kitsu when required. Sending a lot of requests to Kitsu can become very slow, which is why Prism caches requests in memory to avoid the same requests in the future. For example: When you click a shot in the "Scenefiles" tab in the Project Browser, Prism will requests a list of all tasks of that shot from Kitsu and saves it in a memory cache. When you select the same shot again later on, Prism will use tasklist, which is stored in the cache instead of sending a new requests to Kitsu. In some cases it is needed to clear the memory cache, for example if someone is creating a new task in Kitsu, but the list of tasks for that shot is already cached in a memory in Prism. Without clearing the cache, the new task won't be visible inside Prism. To clear the cache you can press the refresh icon in the Project Browser, restart Prism or you can use the "Clear Cache" option in the "Kitsu" menu in the Prism Project Browser.

## Environment Variables

The Kitsu plugin can be controlled using the following environment variables:

| Name | Description |
| --- | --- |
| PRISM\_KITSU\_URL | Sets the Kitsu URL, which Prism connects to. This overrides the URL in the project settings. (e.g. [https://company.cg-wire.com](https://company.cg-wire.com/)) |
| PRISM\_KITSU\_EMAIL | The email to use for the login. (e.g. [john@company.com](mailto:john%40company.com)) |
| PRISM\_KITSU\_PASSWORD | The api key to use for the login. (e.g. key123) |