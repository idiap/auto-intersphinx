# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/idiap/auto-intersphinx/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                     |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/auto\_intersphinx/\_\_init\_\_.py    |       95 |       10 |       36 |       10 |     85% |154->158, 159, 167-168, 172, 203-204, 243-244, 263, 283->287, 289, 290->exit |
| src/auto\_intersphinx/catalog.py         |      250 |       18 |       94 |       13 |     91% |44, 101, 102->121, 103->102, 112->102, 115-116, 152-153, 165-166, 222->225, 228, 232->225, 285-287, 312, 321, 508, 522-525, 606 |
| src/auto\_intersphinx/check\_packages.py |       65 |        0 |       32 |        3 |     97% |69->75, 75->38, 78->38 |
| src/auto\_intersphinx/cli.py             |       18 |        0 |        2 |        1 |     95% |  19->exit |
| src/auto\_intersphinx/dump\_objects.py   |       19 |        0 |        2 |        0 |    100% |           |
| src/auto\_intersphinx/update\_catalog.py |       76 |        1 |       30 |        2 |     97% |70->73, 82 |
|                                **TOTAL** |  **523** |   **29** |  **196** |   **29** | **92%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/idiap/auto-intersphinx/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/idiap/auto-intersphinx/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/idiap/auto-intersphinx/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/idiap/auto-intersphinx/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fidiap%2Fauto-intersphinx%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/idiap/auto-intersphinx/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.