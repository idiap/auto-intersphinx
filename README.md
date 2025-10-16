# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/idiap/auto-intersphinx/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                     |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/auto\_intersphinx/\_\_init\_\_.py    |       95 |       78 |       36 |        0 |     13% |65, 91-109, 147-297, 308-323 |
| src/auto\_intersphinx/catalog.py         |      292 |       72 |      108 |       22 |     72% |46, 98, 105-111, 133, 134->153, 135->134, 144->134, 147-148, 181-185, 200, 201->207, 213-216, 226-229, 260, 264->276, 283->286, 289, 293->286, 347-349, 379, 388, 470->475, 593->617, 596, 612-615, 664-668, 693-742, 754-755, 769-776, 801-805 |
| src/auto\_intersphinx/check\_packages.py |       66 |        0 |       32 |        3 |     97% |69->75, 75->38, 78->38 |
| src/auto\_intersphinx/cli.py             |       18 |        0 |        0 |        0 |    100% |           |
| src/auto\_intersphinx/dump\_objects.py   |       19 |        0 |        2 |        0 |    100% |           |
| src/auto\_intersphinx/update\_catalog.py |       78 |        1 |       28 |        2 |     97% |70->73, 82 |
|                                **TOTAL** |  **568** |  **151** |  **206** |   **27** | **70%** |           |


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