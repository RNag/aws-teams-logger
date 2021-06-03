# Contributing

## Quickstart

First activate a virtual environment, and then use the `make` command
to install the necessary dev dependencies:

```shell
make init
```

## Testing

### Integration

Before running the integration tests, you'll need to:

* Update the values at the top in the [conftest module](tests/conftest.py)

  * If you're using a different AWS profile name, be sure to set the env variable
    `AWS_PROFILE` or override the value for `DEFAULT_PROFILE` in the module 
    to point to the desired AWS environment

* Run `upload_templates` to ensure the necessary SES templates are uploaded
  to your AWS account. There's also a test case for that in case it's easier to run it.

* Ensure the email for `SES_IDENTITY` has been validated in the SES console.
  You can use your personal email if it's easier, as you'll need to verify it first.

* Turn off Sandbox mode in the SES console. This is needed as otherwise we will need
  to verify each recipient email individually, such as the one for the Teams channel.

To run the Integration test suite:

```shell
pytest -v tests/integration
```

If you want to run ALL tests instead, pass the `--run-all` option.

### Unit

Runs only the mock unit tests.

```shell
pytest -v tests/unit
```

## Deploying

### Bump Version

Use the `make` commands for an easier approach to bump the _major_, _minor_, or _patch_ versions.

Example:
```shell
make bump-minor
```

### Publish

First, create API tokens and add them to your `~/.pypirc` file.

Then you can use the below commands to deploy to the public PyPI.
#### Deploy to Test PyPI

```shell
make publish-test
```

#### Deploy to PyPI

```shell
make publish
```
