## Folder Structure

This is the default project folder structure:

00\_Pipeline: This folder contains configs, error logs and other files, which Prism needs or creates. It also contains folders where you can add Prism plugins or python modules to this project. There are also "hooks", some python scripts in which you can run your custom python code on specific event. Usually you don't need to touch the 00\_Pipeline folder.

01\_Management: This folder is intended for schedule and management documents. It's not required by Prism and Prism won't create any files in it. The folder can be safely deleted at any time.

02\_Designs: This folder is intended for concepts, moodboards, design references and so on. Like the previous folder this folder is not required by Prism and can be safely deleted.

03\_Production: This is the place where Prism creates all the assets and shots of you project. All the scenefiles, caches, playblasts and renders are saved here. If you delete this folder then you will delete all your assets and shots.

04\_Resources: This folder is intended for textures, HDRIs and other files, which are not specific to one asset or a shot. Prism gives you the option to safe textures and Houdini HDAs inside this folder.

In all folders you can create your own subfolders if needed. Except the 00\_Pipeline folder you can delete all other folders and Prism will recreate any folder when it's needed.

Each asset and each shot has an "Export", "Playblasts", "Renders" and "Scenefiles" subfolder. In "Export" Prism will save caches, USD compositions and any geometry, which you export from your DCC. In the Project Browser you can browse these files in the "Products" tab. The other three folder should be self-explanatory.

The structure of all folders where Prism saves files to can be changed using template paths in the "Folder Structure" tab of the project settings window.