## Alembic Workflow

The following document describes how to configure Prism for a Maya-Alembic referencing workflow.

**Included Departments:** Modeling, Surfacing, Rigging, Animation, Lighting

The goal is to automate the workflow from Modeling to Lighting as much as possible, ensuring that artists no longer need to worry about the import process or deal with export settings, allowing them to focus on their actual tasks.

This involves various steps, such as importing necessary products for each department and applying pre-configured export settings based on the relevant department.

## Prerequisites

### Disable USD

If the USD Plugin is enabled for other projects, it can be disabled explicitly for the Maya-Alembic referencing workflow project:

`Prism Settings > Project > General > Disabled Plugins > Open the dropdown > Select USD`

### Add State Defaults

To take full advantage of the Maya Alembic referencing workflow, default export settings can be configured in advance based on:

- **Entity** (e.g., Characters, Environments, Sequences, Shots)
- **Department** (e.g., Modeling, Animation, Lighting)
- **Task** (e.g., Texturing, Animation, Compositing)

For example, if a default "Export" state is set for Surfacing, it automatically applies to all Surfacing tasks. This eliminates the need for artists to manually configure export settings each time.

Default "Export" state for Modeling:

Create an "Export" state via the Project Settings:

`Prism Settings > Project > States > State Defaults > "+" > Export`

Open the "State Settings" via the "wheel" icon and apply the following settings:

![[Maya-Alembic - Export State for Assets]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya-Alembic_ExportStateAssets.png)

Open the "Default for" settings via the "pen" icon and add the "Modeling" task from the dropdown list (1):

![[Maya-Alembic - Default For]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya-Alembic_DefaultFor.png)

Default "Export" state for Surfacing:

Create an "Export" state via the Project Settings:

`Prism Settings > Project > States > State Defaults > "+" > Export`

Open the "State Settings" via the "wheel" icon, set the "Productname" to "Surfacing" and apply the same settings as those used in Modeling.

In addition, enable "Remove Namespaces" in the "Additional Settings..." of the "State Settings".

Open the "Default for" settings via the "pen" icon and add "Surfacing" from the dropdown list next to "Tasks".

Default "Export" state for Rigging:

Create an "Export" state via the Project Settings:

`Prism Settings > Project > States > State Defaults > "+" > Export`

Open the "State Settings" via the "wheel" icon, set the "Productname" to "Rigging" and apply the same settings as those used in Modeling.

Open the "Default for" settings via the "pen" icon and add "Rigging" from the dropdown list next to "Tasks".

Default "Export" state for Animation:

Create an "Export" state via the Project Settings:

`Prism Settings > Project > States > State Defaults > "+" > Export`

Open the "State Settings" via the "wheel" icon and apply the following settings:

![[Maya-Alembic - Export State for Animation]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya-Alembic_ExportStateAnimation.png)

Open the "Default for" settings via the "pen" icon and add "Animation" from the dropdown list.

Summary of default "Export" states:

The following "Export" states have been created:

`Prism Settings > Project > States > State Defaults`

![[Maya-Alembic - Export States]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya-Alembic_ExportStates.png)

### Scene Building Settings

Product Tags:

All exported products will be tagged by default. This helps Prism to identify which products should be imported into specific departments or tasks during Scene Building.

Default "Product Tags" are available in the Project Settings:

`Prism Settings > Project > General > Product Tags > Manage Product Tags`

![[Maya-Alembic - Product Tags]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya-Alembic_ProductTags.png)

The Maya Alembic referencing workflow, uses the default predefined "Product Tags". No change is needed to proceed.

Maya - Scene Building Settings:

All Scene Building steps can be configured via the Prism Settings:

`Prism Settings > Project > Scene Building > Maya`

The following steps will be configured:

![[Maya-Alembic - Scene Building Settings]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya-Alembic_SceneBuildingSettings.png)

**Keep the default settings for:**

Set Framerange

Set FPS

Import Shot Cameras

**Adjust the settings for:**

Create Model Hierarchy (Modeling)

Import Products (Modeling + Surfacing)

Import Products (Rigging)

Import Products (Animation)

Apply Alembic Caches (Lighting)

**Create Model Hierarchy (Modeling):**

Open the step settings (Edit Settings...) via the "wheel" icon.

In the "Step Settings - Create Model Hierarchy" window, open the "Apply to tasks" settings via the "pen" icon, then add "Modeling" from the dropdown list to set the following selection: `*-*-Modeling`

**Import Products (Modeling + Surfacing):**

Open the step settings (Edit Settings...) via the "wheel" icon.

In the "Step Settings - Import Products" window, open the "Apply to tasks" settings via the "pen" icon, then add "Modeling" and "Surfacing" from the dropdown list to set the following selection: `*-*-Modeling, Surfacing`

Set the "Mode" to `Reference`.

**Import Products (Rigging):**

Open the step settings (Edit Settings...) via the "wheel" icon.

In the "Step Settings - Import Products" window, open the "Apply to tasks" settings via the "pen" icon, then add "Rigging" from the dropdown list to set the following selection: `*-*-Rigging`

Set the "Mode" to `Import`.

Clear the default variables `{entity}_{task}` from the "Namespace" field. This field should be left blank.

Enable the "Ignore Master Versions" checkbox.

**Import Products (Animation):**

Open the step settings (Edit Settings...) via the "wheel" icon.

In the "Step Settings - Import Products" window, open the "Apply to tasks" settings via the "pen" icon, then add "Animation" from the dropdown list to set the following selection: `*-*-Animation`

Set the "Mode" to `Reference`.

**Apply Alembic Caches (Lighting):**

Open the step settings (Edit Settings...) via the "wheel" icon.

In the "Step Settings - Apply Alembic Caches" window, open the "Apply to tasks" settings via the "pen" icon, then add "Lighting" from the dropdown list to set the following selection: `*-*-Lighting`

## Modeling

Scene Building Modeling:

Launch Maya and open the Project Browser inside Maya.

Run the Scene Building in the Modeling task of an selected Asset (see "Access Scene Building").

An initial scenefile "v0001" with the comment "Scene Building" has been created.

All specified Scene Building steps have been executed. This includes the "Create Model Hierarchy" step which creates a basic structure to work with:

![[Maya-Alembic - Model Hierarchy]](https://prism-pipeline.com/docs/latest/_static/plugins/maya/Maya-Alembic_ModelHierarchy.png)

Export Modeling:

The model can be published (exported) to make it available for downstream departments.

As the prerequisite "State Defaults" have already been created, the model can now be exported using the Prism Export tool via the tool shelf.

The Export window shows that Prism has detected and preselected the model based on the asset name and hierarchy, as well as the "State Defaults" set for Modeling.

Add a comment and confirm by clicking "Export".

The model has been published as "Modeling" product, and since the default "Product Tags" are in place, the product has been tagged with `to_surf` to make it available to the Surfacing department.

## Surfacing

Scene Building Surfacing:

Launch Maya and open the Project Browser inside Maya.

Run the Scene Building in the Surfacing task of an selected Asset (see "Access Scene Building").

An initial scenefile "v0001" with the comment "Scene Building" has been created.

All specified Scene Building steps have been executed. This includes the "Import Products" step which imports (reference) the Modeling product.

Export Surfacing:

The model can be published (exported) to make it available for downstream departments.

As the prerequisite "State Defaults" have already been created, the model can now be exported using the Prism Export tool via the tool shelf.

The Export window shows that Prism has detected and preselected the model based on the asset name and hierarchy, as well as the "State Defaults" set for Surfacing.

Add a comment and confirm by clicking "Export".

The model has been published as "Surfacing" product, and since the default "Product Tags" are in place, the product has been tagged with `to_rig` to make it available to the Rigging department.

In addition, the "Surfacing" product has been tagged with `static` to indicate that it is the target for the animation cache in Lighting. This tag ensures that the product is imported and that the animation cache is applied to it.

## Rigging

Scene Building Rigging:

Launch Maya and open the Project Browser inside Maya.

Run the Scene Building in the Rigging task of an selected Asset (see "Access Scene Building").

An initial scenefile "v0001" with the comment "Scene Building" has been created.

All specified Scene Building steps have been executed. This includes the "Import Products" step which imports (import) the Surfacing product.

Export Rigging:

The model can be published (exported) to make it available for downstream departments.

As the prerequisite "State Defaults" have already been created, the model can now be exported using the Prism Export tool via the tool shelf.

The Export window shows that Prism has detected and preselected the model based on the asset name and hierarchy, as well as the "State Defaults" set for Rigging.

Add a comment and confirm by clicking "Export".

The model has been published as "Rigging" product, and since the default "Product Tags" are in place, the product has been tagged with `to_anm` to make it available to the Animation department.

## Animation

Connect Assets:

Before work on a shot can begin, the required assets have to be linked. These assets will then be loaded during Scene Building.

Right-click on any shot in the Project Browser and and click "Connect Assets...".

In the "Connect Entities" window select all required assets.

Confirm with "Apply" and a popup window shows all connected assets.

Scene Building Animation:

Launch Maya and open the Project Browser inside Maya.

Run the Scene Building in the Animation task of an selected Shot (see "Access Scene Building").

An initial scenefile "v0001" with the comment "Scene Building" has been created.

All specified Scene Building steps have been executed. This includes the "Import Products" step which imports (reference) the Rigging products of all connected assets.

Export Animation:

Animation caches can be published (exported) to make them available for downstream departments.

As the prerequisite "State Defaults" have already been created, the animation caches can now be exported using the "Prism Batch Export" tool via the tool shelf.

Right-click on the Export icon in the tool shelf and select "Export Multiple Assets...".

The "Batch Export" window shows that Prism has detected all available asset. For each found asset, "Identifiers" have been defined and the "geo" subgroup have been selected.

Confirm by clicking "Export".

The "Prism Batch Export" tool will create export states for each detected asset and uses the "State Defaults" set for Animation.

Animation caches have been published, and since the default "Product Tags" are in place, all products have been tagged with `animated` to make them available to the Lighting department.

## Lighting

Scene Building Lighting:

Launch Maya and open the Project Browser inside Maya.

Run the Scene Building in the Lighting task of an selected Shot (see "Access Scene Building").

An initial scenefile "v0001" with the comment "Scene Building" has been created.

All specified Scene Building steps have been executed. This time instead of using the "Import Products" step, the "Apply Alembic Caches" step have been executed.

This step checks for available animation caches. For each found cache the corresponding Surfacing product which is tagged with `static` will be referenced.

Subsequently, the animation caches will be applied to each referenced Surfacing product.

Render Lighting:

Once everything is set the shot can be rendered using the "Prism Render" tool via the tool shelf.

Configure the settings, add a comment and confirm by clicking "Render".

The render output can be reviewed in the "Media" tab of the Project Browser.

## Benefits

- If Modeling is updating the model, Surfacing will automatically receive the update the next time the scenefile gets loaded.
- If Surfacing is updating materials, Lighting will automatically receive the update the next time the scenefile gets loaded.
- If Animation is updating animations, Lighting will automatically receive these updates.

## Limitations

- Whenever the model gets changes, Surfacing will get these updates but Rigging needs to reimport the latest product and redo some rigging tasks. However, this approach helps to prevent rigs from breaking.
- The workflow is not entirely using Referencing (for example not during Rigging) to avoid deep references which could lead to several issue in Maya.

While this workflow aims to balance automation and usability, it has some limitations as described above.

For a fully non-destructive and procedural workflow, consider testing and using USD in Maya.