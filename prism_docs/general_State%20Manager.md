## State Manager

The State Manager is a powerful tool to import, export and render in your DCCs.

It consists of two lists on the left side: one for imports and one for exports. You can import products into your scenefiles by adding new import states to the import list.

In the export list you can add export states, render states and playblast states.

Depending on your DCC and your installed plugins, there might be many more state types available.

By clicking the publish button at the bottom of the State Manager, as the states in the export list will be executed from top to bottom.

## Rendering every x frame

To render only every x frame, the "Framerange" setting on the ImageRender state in the Prism State Manager can be set to "Expression".

You can specify a framerange and add "x4" to render only every 4th frame.

Replace the last number to control, which frames will be rendered.

For example: "1001-1100x2" will render every second frame and "50-200x5" will render every 5th frame.

The tooltip of the expression field provides some more examples and a preview, which frames will be rendered with your expression.