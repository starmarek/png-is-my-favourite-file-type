# png-is-my-favourite-file-type

This is an app for png analysis. It allow you to:
- Extract metadata
- Print your png
- Print spectrum diagram via FFT
- Remove unnecessary rubbish from you file

## How to run it

Use the runner script:
```bash
./png_run.sh {command}
```
Where **command** is one of:
- metadata
- print

For flags that you can pass to runner script type:
```bash
./png_run.sh --help
```
### How to use your own file

Runner script is using the default png image: `png_files/dice.png`, however if you want to use your own file you must use `--file-name` flag.

E.g.
```bash
./png_run.sh print --file-name=/home/adam/files/mypng.png
```
### More detailed explanation
App is using [*fire*](https://github.com/google/python-fire) package as a command line interface. 

In the *png_run.sh* you can find:

```bash
CLI_ENTRYPOINT=app/cli.py
(...)
python3.8 $CLI_ENTRYPOINT "$@"
```

Which means that you are actually running methods from `CLI` class from `app/cli.py` file.

In mentioned file:

```python
class CLI():
(...)
if __name__ == '__main__':
    fire.Fire(CLI)
```

If you are interested in fire project please look at [*fire github page*](https://github.com/google/python-fire).
