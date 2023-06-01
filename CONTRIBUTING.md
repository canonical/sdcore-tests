# Contributing

To make contributions to this projec, you'll need a working [Juju development setup](https://juju.is/docs/sdk/dev-setup).

You can use the environments created by `tox` for development:

```shell
tox --notest -e integration
source .tox/integration/bin/activate
```

## Testing

This project uses `tox` for managing test environments. There are some pre-configured environments
that can be used for linting and formatting code when you're preparing contributions to the project:

```shell
tox -e fmt           # Format code
tox -e lint          # Code style
tox -e static        # Static analysis
tox -e integration   # Integration tests
```
