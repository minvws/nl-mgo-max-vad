# Contributing to MGO DVP Proxy

Thank you for considering contributing to the MGO VAD! We welcome contributions from everyone. Below are some guidelines to help you get started.

## How to Report Issues

If you encounter any issues or have suggestions for improvements, please feel free to open an issue on the GitHub repository. When reporting an issue, please include as much detail as possible, including steps to reproduce the issue and any relevant logs or screenshots.

## How to Submit Pull Requests

1. Fork the repository and create your branch from `develop`.
2. If you have added code that should be tested, add tests.
3. Ensure the test suite passes (`make test`).
4. Make sure your code lints (`make lint`).
5. Make sure your code passes the analyzers (`make check`).
6. Submit a pull request to the `develop` branch with a clear description of your changes.

## Coding Standards

- Follow the existing coding style.
- Adhere to the existing [directory structuring guidelines](https://github.com/zhanymkanov/fastapi-best-practices?tab=readme-ov-file#project-structure)
- Write clear and concise commit messages.
- Include comments in your code where necessary.

## Visual Studio Code

This repository contains shared configuration files, which automates the setup
of your workspace.

The configuration files reside in the `./.vscode` folder.

VS Code will detect this folder automatically and will recommend that you
install several extensions. It is advised to install all of them, as it will be
a good starting point for this project.

## Developing inside a Container

Once you have installed all the extensions, VS Code may detect a Dev Container
configuration file and, hence, ask you to reopen the folder to develop in a
container.

This feature is enabled by the Dev Container extension. It allows you to use a
container as a full-featured development environment, providing a better
development experience, including auto-completion, code navigation, and
debugging.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

Thank you for your contributions!