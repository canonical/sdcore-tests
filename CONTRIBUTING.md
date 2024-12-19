# Contributing

To make contributions to this project, you'll need a working [Juju development setup](https://juju.is/docs/sdk/dev-setup).

This project uses `uv`. You can install it on Ubuntu with:

```shell
sudo snap install --classic astral-uv
```

You can create an environment for development with `uv`:

```shell
uv sync
source .venv/bin/activate
```

## Testing
This project uses `tox` for managing test environments. It can be installed
with:

```shell
uv tool install tox --with tox-uv
```

There are some pre-configured environments
that can be used for linting and formatting code when you're preparing contributions to the charm:

```shell
tox -e fmt           # Format code
tox -e lint          # Code style
tox -e static        # Static analysis
tox -e integration   # Integration tests
```
