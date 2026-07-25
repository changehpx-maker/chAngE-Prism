## Licensing

2026-03-02

12 min read

## Plans

You can find an overview of the available plans and purchase licenses [here](https://prism-pipeline.com/plans).

The same installer is used for all plans and can be downloaded from [here](https://prism-pipeline.com/downloads).

### Free

### Plus

### Pro

### Educational

### Non-Commercial

### Other Services

## License File

A license file can be used to specify license information for one or multiple workstations and to skip the manual login in the login dialog.

This can be useful when automating the setup of workstations like on a renderfarm.

To use a license file set the environment variable `PRISM_LICENSE_FILE` to a json filepath, where you want to save the license file. For example `C:/files/prism_licenses.json`.

This file doesn't need to exist yet.

There are two ways how to add content to the license file.

The easier way is to launch Prism with the `PRISM_LICENSE_FILE` environment variable defined.

Prism will then create the file if it doesn't exist and add it's mac address to it.

The other option is to manually add the mac addresses of your workstations to the json file.

The simplest form of a license file looks like this:

```
{
    "default": {
        "access_token": "<your_token_here>"
    }
}
```

It can be extended with additional options like this:

```
{
    "auto_add_workstations": false,
    "default": {
        "access_token": "<your_token_here>",
        "preferred_license": "Plus"
    },
    "workstations": {
        "F2:C9:AB:0A:7A:29": {
            "name": "WS-001",
            "access_token": "<your_token_here>",
            "preferred_license": "Plus"
        },
        "FB:97:23:4D:6D:55": {
            "name": "WS-002",
            "access_token": "<your_token_here>",
            "preferred_license": "Free"
        }
    }
}
```

You can edit the file in a text editor and fill out the `access_token` field for the workstation.

To generate an access token see.

You can also specify an `access_token` under the `default` key.

It will be used by workstations, which don't have an `access_token` assigned under the `workstations` key.

Only access tokens can be used in license files at this point.

Usernames and passwords are not supported because of security considerations as the license file is not encrypted.

`auto_add_workstations` can be set to `true` to add workstations automatically to the list of workstations, when they are accessing the license file. This option is available since v2.0.7. In previous versions it was the default behavior, that workstations were added to the file automatically.

If you are using offline licensing you can specify an `activation_code` in place of the `access_token`.

The `preferred_license` key can be used to let workstations acquire a specific license type if a license of that type is available.

## Offline Licensing

The offline licensing is available in the Prism Pro plan.

After purchasing Pro licenses please [contact us](https://prism-pipeline.com/contact) to get access to a specific offline installer.