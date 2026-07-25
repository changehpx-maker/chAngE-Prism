![[Logo: Project Management]](https://prism-pipeline.com/docs/latest/_static/banner_logos/projectmanagement_logo.png)

## Project Management

The ProjectManagement plugin adds new features to Prism, which help teams to manage their tasks and track their project progress.

## Overview

By using this plugin a "Project Manager" (also called manager backend) can be set for each Prism project. Each manager backend can have different features, for example publishing media to 3rd party management tools. The standard Prism manager backend has the following features:

- assign a status to a task (displayed using a color/icon on each task in the Project Browser)
- assign a status to a product version (displayed using a color/icon on each task in the Project Browser)
- assign a status to a media version (displayed using a color/icon on each task in the Project Browser)
- create and view notes on tasks, product versions and media versions
- assign tasks to artists
- artists can view their assigned tasks

Additional manager backends are currently available for [FTrack](https://prism-pipeline.com/docs/latest/plugins/FTrack/#plugin-ftrack), [Kitsu](https://prism-pipeline.com/docs/latest/plugins/Kitsu/#plugin-kitsu) and [Shotgrid](https://prism-pipeline.com/docs/latest/plugins/Shotgrid/#plugin-shotgrid). More official manager backends as well as manager backends created by 3rd party developers might become available in the future.

## Setup

The manager backend of a Prism project can be set in the Project Settings. In the tab "Project Management" a dropdown allows to choose from all currently available manager backends. "Prism" is the standard manager backend, which is always available when this plugin is loaded. It's features are listed above. If "None" is selected then no features are added by the ProjectManagement plugin and Prism can be used in the same way as if this plugin would be disabled.

## Task assignments

Tasks can be assigned to users in the "Scenefiles" tab of the Prism Project Browser. Select a task and choose "Manage assignment..." from the rightclick menu. A window opens where you can enter a Prism username to which the task should be assigned as well as a start and end date.

Users can view their assigned tasks in the "Tasks" tab in the Prism Project Browser. Here they can view and filter their assigned tasks and view/add notes to the tasks.

## Environment Variables

The Project Management plugin can be controlled using the following environment variables:

| Name | Description |
| --- | --- |
| PRISM\_PRJMNG\_IGNORE\_STUDIO\_USER\_WARNING | Disables the warning popup when the username in Prism cannot get changed to the Shotgrid/ftrack/Kitsu username, because the new username doesn't exist in the Studio settings, when the Studio plugin is enabled. (e.g. 1 or 0, default: 0) |