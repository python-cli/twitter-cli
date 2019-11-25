# twitter-cli

> Parse and download the tweets from home timeline, specified user timeline, favorites list.



#### Usage

```shell
➜  ~ twitter-cli --help
Usage: twitter-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --debug / --no-debug  Enable logger level to DEBUG
  --help                Show this message and exit.

Commands:
  credential  Verify the current user credential.
  favorites   Fetch the user's favorite statuses.
  timeline    Fetch the specified user's timeline.
➜  ~ twitter-cli credential --help
Usage: twitter-cli credential [OPTIONS]

  Verify the current user credential.

Options:
  --help  Show this message and exit.
➜  ~ twitter-cli timeline --help
Usage: twitter-cli timeline [OPTIONS] [USERNAME]

  Fetch the specified user's timeline.

Options:
  --download-media / --no-download-media
                                  Download status's media files or not
  --help                          Show this message and exit.
➜  ~ twitter-cli favorites --help
Usage: twitter-cli favorites [OPTIONS]

  Fetch the user's favorite statuses.

Options:
  --from-latest / --from-last     Fetch statuses from latest or last saved one
  --download-media / --no-download-media
                                  Download status's media files or not
  --destroy / --no-destroy        Destroy the favorite statuses
  --schedule INTEGER              Run as scheduler with specified hours
  --help                          Show this message and exit.
➜  ~
```



#### Author

[Will Han](https://xingheng.github.io)
