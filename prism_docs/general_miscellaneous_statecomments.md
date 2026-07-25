Enabling a comment field for every state in the State Manager

## Enabling Comments per State

There is a comment field in the Prism State Manager above the Publish button, where you can enter a comment, which will be used for all products and renders, which will be executed during the next publish.

If you have multiple exports or renders and you would like to use different comments for each of them, you can enable a comment field for each individual state.

To enable comments per state set the environment variable `PRISM_USE_STATE_COMMENTS` to `1`.

You can set environment variables in the Prism User Settings, Project Settings or Studio Settings.

![../../../_images/state_comments.jpg](https://prism-pipeline.com/docs/latest/_images/state_comments.jpg)

> [!note] Note
> If the comment field of a state is empty, the value in the comment field above the Publish button in the State Manager will be used.