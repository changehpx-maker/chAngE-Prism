![[Logo: Shotgrid]](https://prism-pipeline.com/docs/latest/_static/banner_logos/shotgrid_logo.png)

## Shotgrid

The Shotgrid plugin connects Prism to [Autodesk Shotgrid](https://www.shotgridsoftware.com/), a project management tool focused on VFX and animation projects.

## Overview

Using this plugin artists can publish media from Prism to Shotgrid, see their assigned tasks in Prism and more. To use this plugin the following prerequisites are required:

- an active Shotgrid site (either a payed site or a free trial site)
- the API access for the Shotgrid user account needs to be enabled (see below)
- the "ProjectManagement" Prism plugin needs to be installed and loaded.

The Shotgrid plugin has the following features:

- display Shotgrid assets, shots and tasks in Prism
- publish media and product versions to Shotgrid
- view and set the Shotgrid status of tasks, product versions and media version
- create and view notes and replies on tasks, product versions and media versions
- view assigned tasks in the Project Browser
- open the Shotgrid page of any entity in a webbrowser directly from Prism

## Setup

To activate the Shotgrid plugin for your currently active Prism project open the Prism Project Settings window and go the the "Project Management" tab.

In the "Manager" dropdown select "Shotgrid".

Next press the "Setup" button, which will guide you through a setup process, in which you have to enter your Shotgrid URL and your account credentials to login.

After Prism could login successfully in the setup dialog, you will see a list of your existing Shotgrid projects.

Select the one you want to connect to Prism and click next.

On the next page you can select to which Prism project you want to connect it to. In most cases this will be your current Prism project, which is the first one in the list, which is already selected.

Click next and now Prism is downloading the thumbnails of your assets and shots. That can take a few seconds depending on how much entities there are in your Shotgrid project.

Once the setup is completed the Shotgrid URL and the project name are added to the Prism Project Settings window. The User account credentials can be accessed in the "Project Management" tab of the Prism User Settings.

You can customize the statuses, which can be assigned to tasks, product versions and media versions in the Prism Project Settings, but these statuses should always be named the same as in Shotgrid.

## Authentication

In order to query information from Shotgrid and to update/create data in Shotgrid, Prism needs to authenticate to Shotgrid. There are 3 different ways how Prism can authenticate to Shotgrid:

This is the default authentication method. A window will popup, where the artists can login with their Autdesk Account. The login can be done in a browser window. This method also supports 2FA. Because this method requires user interaction, it cannot be used when running Prism in Nogui mode.

This method allows the users to login with their legacy Shotgrid login credentials.

To use this method go to the user account page in Shotgrid and go to "Legacy Login and Personal Access Token". A password needs to be set and a personal access token needs to be connected. To generate the personal access token follow the instructions in the Autodesk documentation [here](https://help.autodesk.com/view/SGSUB/ENU/?guid=SG_Migration_mi_migration_account_mi_end_user_account_html#generating-your-personal-access-token).

On the user workstation set the env var `PRISM_SHOTGRID_USE_DEPR_AUTH` to `1`. Users can then enter their email and password in the Prism User Settings -> Project Management.

Alternatively you can also use the `PRISM_SHOTGRID_EMAIL` and `PRISM_SHOTGRID_PASSWORD` env vars.

3\. **Script based authentication**

In the Shotgrid Admin settings you can create new "Scripts". These scripts have a name, an API key and permissions. These scripts can then be used to authenticate Prism to Shotgrid.

After creating a new Script in Shotgrid, set the `PRISM_SHOTGRID_USE_SCRIPT_AUTH` env var to `1` and set the `PRISM_SHOTGRID_SCRIPTNAME` and `PRISM_SHOTGRID_APIKEY` to the name and api key of the SG Script.

## Assets, Shots and Tasks

In the "Scenefiles" tab of the Prism Project Browser you can view all assets, shots, departments and tasks, which exists in Shotgrid. The thumbnails, description (for assets) and the framerange (for shots) will be synced from Shotgrid as well. The folders of the tasks might not exist in your Prism project folder yet, but as soon as a scenefiles gets saved under a task, all the required folders will be created.

Assets and shots have to be created in Shotgrid and cannot be created inside Prism if the Shotgrid plugin is active. Departments and tasks have to be created in Shotgrid as well by default, but in the Prism project settings you can enable the creation of local departments and tasks, which don't exist in Shotgrid.

If you have any assets, shots, tasks, product versions or media versions in Shotgrid, which you don't want to be visible inside Prism, you can assign them a "noPrism" tag in Shotgrid.

You can rightclick any asset, shot or task and open it's page in Shotgrid in a webbrowser.

Tasks have a status icon before the name and a tooltip with the status name. This status can be changed from the rightclick menu or in Shotgrid.

You can also access Shotgrid notes on a task from the "Show Notes..." option in the rightclick menu of a task. This opens a window, where you can view and create Shotgrid notes and replies.

To view the Shotgrid tasks, which are assigned to the currently loggedin user, you can open the "Tasks" tab in the Prism Project Browser. Here you can see a list of all your assigned tasks, as well as their status and their start/end dates. You can filter the displayed tasks by their status using the checkboxes at the bottom of the page. On the right side you can view and create notes for the currently selected task. You can doubleclick a task item to jump directly to the scenefiles of this task.

## Product versions

Product versions can be published from the "Products" tab in the Prism Project Browser to Shotgrid. The product file itself will not be uploaded. Instead Prism will create a version entity in Shotgrid with the local filepath attached to it. After a product version is published to Shotgrid, the status for the product versions can be set and notes can be viewed/created from the rightclick menu of the version.

If a product version is getting published to Shotgrid, it will be created on the task, which matches the product name in Prism. If no matching task is found in Shotgrid Prism will ask you to select a Shotgrid task from a list, to which one the version will be published. In the Prism Project Settings this option can be disabled ("Allow publishes from non-existent tasks").

## Media versions

Media versions like renders and playblasts can be published from the "Media" tab in the Prism Project Browser to Shotgrid using the rightclick menu on the media thumbnail or the version item. Prism will create a version entity in Shotgrid with the local filepath attached to it. Optionally you can also add a description and let Prism upload a proxy version of your media, which can be reviewed inside of Shotgrid. After a media version is published to Shotgrid, the status for the media versions can be set and notes can be viewed/created from the rightclick menu of the version.

If a media version is getting published to Shotgrid, it will be created on the task, which matches the identifier name in Prism. If no matching task is found in Shotgrid Prism will ask you to select a Shotgrid task from a list, to which one the version will be published. In the Prism Project Settings this option can be disabled ("Allow publishes from non-existent tasks").

## Memory Caching

Prism queries assets, shots, tasks and more directly from Shotgrid when required. Sending a lot of requests to Shotgrid can become very slow, which is why Prism caches requests in memory to avoid the same requests in the future. For example: When you click a shot in the "Scenefiles" tab in the Project Browser, Prism will requests a list of all tasks of that shot from Shotgrid and saves it in a memory cache. When you select the same shot again later on, Prism will use tasklist, which is stored in the cache instead of sending a new requests to Shotgrid. In some cases it is needed to clear the memory cache, for example if someone is creating a new task in Shotgrid, but the list of tasks for that shot is already cached in a memory in Prism. Without clearing the cache, the new task won't be visible inside Prism. To clear the cache you can press the refresh icon in the Project Browser, restart Prism or you can use the "Clear Cache" option in the "Shotgrid" menu in the Prism Project Browser.

## Troubleshooting

The first thing to check is if all your login details are correct.

If the login details are correct, but the login is still not successful, the account might be locked temporarily. This can happen after entering the password incorrectly multiple times, which will lock the API access temporarily.

You can either wait (usually 1 hour) or remove the lock in Shotgrid in your browser.

Go to the user page of the locked user. In the "Person Info" section display all "All Info" and remove the value in the "Locked Until" field.

## Environment Variables

The Shotgrid plugin can be controlled using the following environment variables:

| Name | Description |
| --- | --- |
| PRISM\_SHOTGRID\_URL | Sets the Shotgrid URL, which Prism connects to. This overrides the URL in the project settings. (e.g. [https://company.shotgrid.autodesk.com](https://company.shotgrid.autodesk.com/)) |
| PRISM\_SHOTGRID\_USE\_DEPR\_AUTH | Enables the deprecated, legacy login method using the Personal Access Token. (e.g. 1 or 0, default: 0) |
| PRISM\_SHOTGRID\_EMAIL | The email to use for the deprecated login method. (e.g. [john@company.com](mailto:john%40company.com)) |
| PRISM\_SHOTGRID\_PASSWORD | The password to use for the deprecated login method (e.g. password123) |
| PRISM\_SHOTGRID\_USE\_SCRIPT\_AUTH | Enables the script authentication instead of the user based authentication. (e.g. 1 or 0, default: 0) |
| PRISM\_SHOTGRID\_SCRIPTNAME | The script name when using the script authentication. (e.g. my\_script) |
| PRISM\_SHOTGRID\_APIKEY | The api key when using the script authentication. (e.g. sg\_key123) |
| PRISM\_PRJ\_MNG\_SHOW\_DEMO\_PROJECTS | Show demo projects in the list of Shotgrid projects. (e.g. 1 or 0, default: 1) |