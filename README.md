# png-is-my-favourite-file-type

This is an app for png analysis. It allow you to:
- Extract metadata
- Print spectrum diagram via FFT
- Remove unnecessary rubbish from you file

## How to run it
### TL;DR 

Type into your command line:
```bash
./png_run.sh {command} {--file=<path-to-your-png-file>} [args]
```
Where **command** is one of:
- metadata
- print
- spectrum
- clean
- fullservice

Where **args** are:
- --verbose

### More detailed explanation
App is using [*fire*](https://github.com/google/python-fire) package as a simple CLI. 

In the *png_run.sh* you can find:

```bash
CLI_ENTRYPOINT=app/cli.py
(...)
python3 $CLI_ENTRYPOINT "$@"
```

Which means that you are actually running methods/functions which are configured to work with *fire* package from `app/cli.py` file.

In mentioned file:

```python
class CLI():
(...)
if __name__ == '__main__':
    fire.Fire(CLI)
```

So as you see all methods of ```CLI``` class are configured to work with *fire* package. For more detailed explanation please take a look at [*fire guide*](https://github.com/google/python-fire/blob/master/docs/guide.md).

